"""
PRISM Honest Allocation Benchmark
=================================
Replaces the measurement path of scripts/run_10gb_master_pipeline.py and
kaggle/run_on_kaggle.py, which (a) never applied the chosen allocation to Spark
(every strategy ran in the same local[N] JVM) and (b) synthesised latencies
for (query, strategy) pairs that had no recorded run.

Cluster model (identical for every strategy):
  * A Spark standalone master + N identical workers (default 4), each sized for
    exactly one executor of a fixed shape (default 2 cores x 1536 MB).
  * Every strategy therefore chooses only HOW MANY executors (1..N) it gets;
    executor cores and memory are the same for all strategies. Model-predicted
    cores/memory are recorded but not applied, so differences between
    strategies cannot come from executor shape.
  * One long-lived application holds the pool; before each run the pool is
    resized to the strategy's count (killExecutor / requestTotalExecutors) and
    waited on until exactly that many executors are registered.
  * spark_dra runs in its own application with real dynamic allocation
    (shuffle tracking), max N executors, reset to 1 executor before each run.

Stage 2 (live): for the *_two_stage strategies a monitor thread watches the
running query through the REST API. When the first shuffle-map stage of the
query completes (the point where AQE re-plans), it reads the real shuffle
bytes written and the real partition count, runs the Stage 2 model, and if the
target is larger than the current pool it grows the pool mid-query with
requestTotalExecutors. Shrinking mid-query is recorded but not applied:
killing an executor that holds shuffle output forces recomputation.

Growth paths (grow_<a>to<b>): the query starts on a executors and, at the same point where live Stage 2
fires (first completed shuffle-map stage, 250 ms polling), the pool is grown to b. This measures the real
mid-query trajectory of every Stage 2 decision a -> b, so replayed Stage 2 configurations are scored on
runs that really started at the Stage 1 count instead of runs that had b executors from the start.

Measurement: one discarded warm-up plus N timed repetitions per unit, a real
timeout (job-group cancel), status/error text instead of a 60 s placeholder,
a result checksum, executor CPU time and allocated core-seconds from Spark's
REST API, and optional K CPU-burner processes for contention runs.

Output: runs.csv (one row per physical run) and decisions.csv. Analyse with
prism/evaluation/analyze_honest_benchmark.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import multiprocessing as mp
import os
import random
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Bind every Spark endpoint to loopback: with the default (the LAN address) a Wi-Fi drop kills
# executor heartbeats and the REST API mid-run, which happened on 2026-10-24 at 14:32.
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
if "JAVA_HOME" not in os.environ and (PROJECT_ROOT / "jdk-17").exists():
    os.environ["JAVA_HOME"] = str(PROJECT_ROOT / "jdk-17")

import joblib
import numpy as np
import pandas as pd
import pyspark
from pyspark.sql import SparkSession

from prism.shared.schemas import CalibrationInput, ClusterCapacity
from prism.calibration.calibrate import calibrate, calibrate_contention_aware
from prism.workload.feature_extractor import extract_submission_features, extract_aqe_features
from prism.plugin.enhanced_dispatcher import PluggableEnhancedDispatcher
from prism.evaluation.multi_classifier_benchmark import sanitize_spark_sql, TPCH_SCHEMAS

STRATEGIES = [
    "static",                     # all N executors
    "fixed_3e",                   # constant rule PRISM must beat (any fixed_<k>e works)
    "heuristic",                  # input-size rule
    "spark_dra",                  # real Spark dynamic allocation
    "prism_stage1_plan_only",     # LightGBM Stage 1, no calibration
    "prism_xgboost",              # Stage 1 + calibration
    "prism_lightgbm",
    "prism_random_forest",
    "prism_ridge",
    "prism_svr",
    "prism_pluggable_enhanced",   # meta-router + CBO hint + memory clamp
    "prism_xgboost_two_stage",    # Stage 1 + live Stage 2 resize
    "prism_lightgbm_two_stage",
]
MODEL_FILES = {"xgboost": "xgboost", "lightgbm": "lightgbm", "random_forest": "model",
               "ridge": "ridge", "svr": "svr", "mlp": "mlp"}
# PRISM-LM bundles (latency model -> executor count) written by prism/model/train_from_sweep.py
MODEL_FILES.update({f"{k}_lm": f"{v}_lm" for k, v in list(MODEL_FILES.items())})


# -----------------------------------------------------------------------------
# Allocation decisions
# -----------------------------------------------------------------------------
@dataclass
class Pool:
    num_workers: int
    executor_cores: int
    executor_memory_mb: int
    contention_k: int = 0
    calibration: str = "original"   # "v2": the 0.9 capacity margin applies only when other jobs load the cluster

    def clamp(self, n: float) -> int:
        return max(1, min(self.num_workers, int(round(n))))

    def calibration_capacity(self) -> ClusterCapacity:
        free_cores = max(self.executor_cores, self.num_workers * self.executor_cores - self.contention_k)
        return ClusterCapacity(available_executors=max(1, free_cores // self.executor_cores),
                               available_cores=free_cores)


@dataclass
class Decision:
    num_executors: int
    dynamic: bool = False
    two_stage_model: str = ""
    sql_conf: Dict[str, str] = field(default_factory=dict)


def load_bundles(models_dir: Path) -> Dict[str, Any]:
    bundles = {}
    for name, stem in MODEL_FILES.items():
        f1, f2 = models_dir / f"stage1_{stem}.joblib", models_dir / f"stage2_{stem}.joblib"
        if f1.exists():
            bundles[name] = {"stage1": joblib.load(f1), "stage2": joblib.load(f2) if f2.exists() else None}
    return bundles


def predict(bundle: Dict[str, Any], fv) -> Tuple[int, int, int]:
    """Raw (executors, cores, memory_mb) prediction of a Stage 1 or Stage 2 bundle."""
    row = {
        "input_size_bytes": fv.plan_features.input_size_bytes,
        "join_order_depth": fv.plan_features.join_order_depth,
        "estimated_shuffle_bytes": fv.plan_features.estimated_shuffle_bytes,
        "stage_dag_depth": fv.plan_features.stage_dag_depth,
        "stage_dag_branch_factor": fv.plan_features.stage_dag_branch_factor,
        "queue_depth": fv.cluster_load_features.queue_depth,
        "available_executors": fv.cluster_load_features.available_executors,
        "available_cores": fv.cluster_load_features.available_cores,
        "colocated_job_count": fv.cluster_load_features.colocated_job_count,
        "true_post_shuffle_bytes": fv.aqe_correction.true_post_shuffle_bytes or 0.0,
        "true_partition_count": fv.aqe_correction.true_partition_count or 0,
    }
    cols = bundle["feature_columns"]
    X = pd.DataFrame([[float(row.get(c, 0.0)) for c in cols]], columns=cols)
    try:
        pred = np.asarray(bundle["model"].predict(X)).reshape(-1)
    except Exception:
        pred = np.asarray(bundle["model"].predict(X.to_numpy())).reshape(-1)
    n_exec = max(1, int(round(pred[0])))
    cores = max(1, int(round(pred[1]))) if len(pred) > 1 else 2
    mem = max(512, int(round(pred[2]))) if len(pred) > 2 else 2048
    return n_exec, cores, mem


def calibrated_count(e: int, c: int, m: int, pool: Pool) -> Tuple[int, bool]:
    if pool.calibration == "v2" and pool.contention_k == 0:
        # idle cluster: original calibrate() would still cap at int(0.9 x N) = N-1 of N (rule fixed 2026-10-25
        # before any v2 measurement; under co-located load v2 is identical to the original)
        return pool.clamp(e), False
    if pool.calibration == "supply":
        # load-aware models (v3 extension) learn the load themselves; calibration only enforces the executor
        # slots the cluster can grant (CPU burners hold none)
        return pool.clamp(e), False
    if pool.calibration == "v3":
        # contention-aware (proposal C4; post-hoc, see calibrate_contention_aware): CPU burners hold no executor
        # slots, so supply = all workers; the CPU they take is the contention signal
        out = calibrate_contention_aware(
            CalibrationInput(predicted_num_executors=e, predicted_executor_cores=c, predicted_executor_memory_mb=m,
                             confidence=0.9, cluster_load=ClusterCapacity(
                                 available_executors=pool.num_workers,
                                 available_cores=pool.calibration_capacity().available_cores)),
            total_executors=pool.num_workers, total_cores=pool.num_workers * pool.executor_cores)
        return pool.clamp(out.calibrated.num_executors), out.used_fallback
    out = calibrate(CalibrationInput(predicted_num_executors=e, predicted_executor_cores=c,
                                     predicted_executor_memory_mb=m, confidence=0.9,
                                     cluster_load=pool.calibration_capacity()))
    return pool.clamp(out.calibrated.num_executors), out.used_fallback


def decide(strategy: str, fv, raw_sql: str, bundles, dispatcher, pool: Pool) -> Tuple[Decision, Dict[str, Any]]:
    t0 = time.perf_counter()
    meta: Dict[str, Any] = {"model": "none", "raw_prediction": "", "calibration_fallback": False}
    in_gb = fv.plan_features.input_size_bytes / 1e9
    if strategy == "static":
        d = Decision(pool.num_workers)
    elif strategy.startswith("fixed_") and strategy.endswith("e"):
        d = Decision(pool.clamp(int(strategy[len("fixed_"):-1])))
    elif strategy == "heuristic":
        d = Decision(pool.clamp(in_gb * 2.5 + 1.0))
    elif strategy == "spark_dra":
        d = Decision(pool.num_workers, dynamic=True)
    elif strategy.startswith("grow_"):
        a, b = (int(x) for x in strategy[len("grow_"):].split("to"))
        d = Decision(pool.clamp(a), two_stage_model=f"__grow{pool.clamp(b)}")
    elif strategy == "prism_stage1_plan_only":
        e, c, m = predict(bundles["lightgbm"]["stage1"], fv)
        meta.update(model="lightgbm", raw_prediction=f"{e}x{c}x{m}")
        d = Decision(pool.clamp(e))
    elif strategy == "prism_pluggable_enhanced":
        plan = dispatcher.plan_stage1_dispatch(fv, bundles, raw_sql=raw_sql)
        sql_conf = {k: v for k, v in plan.spark_conf_overrides.items() if k.startswith("spark.sql.")}
        meta.update(model=plan.selected_model, cbo_injected=plan.cbo_broadcast_injected,
                    memory_clamped=plan.memory_clamped,
                    raw_prediction=f"{plan.num_executors}x{plan.executor_cores}x{plan.executor_memory_mb}")
        d = Decision(pool.clamp(plan.num_executors), sql_conf=sql_conf)
    else:
        m_name = strategy.replace("prism_", "").replace("_two_stage", "")
        e, c, m = predict(bundles[m_name]["stage1"], fv)
        n, fb = calibrated_count(e, c, m, pool)
        meta.update(model=m_name, raw_prediction=f"{e}x{c}x{m}", calibration_fallback=fb)
        d = Decision(n, two_stage_model=m_name if strategy.endswith("_two_stage") else "")
    meta["decision_overhead_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
    return d, meta


# -----------------------------------------------------------------------------
# Data registration
# -----------------------------------------------------------------------------
def register_views(spark: SparkSession, benchmark: str, data_dir: Path) -> None:
    if benchmark == "tpch":
        for table, schema in TPCH_SCHEMAS.items():
            tbl, pq = data_dir / f"{table}.tbl", data_dir / table
            if pq.is_dir():
                df = spark.read.parquet(str(pq))
            elif tbl.exists():
                df = spark.read.option("delimiter", "|").schema(schema).csv(str(tbl))
                df = df.select(*[c for c in df.columns if not c.startswith("_c")])
            else:
                raise FileNotFoundError(f"TPC-H table {table} not found in {data_dir}")
            df.createOrReplaceTempView(table)
    else:
        found = 0
        for p in sorted(data_dir.iterdir()):
            if p.name.startswith("."):
                continue
            if p.is_dir() or p.suffix == ".parquet":
                spark.read.parquet(str(p)).createOrReplaceTempView(p.stem)
                found += 1
        if not found:
            raise FileNotFoundError(f"No TPC-DS parquet tables in {data_dir}")


def split_statements(sql: str) -> Tuple[List[str], str]:
    stmts = [s.strip() for s in sql.split(";") if s.strip()]
    main = [s for s in stmts if s.lower().lstrip("( ").startswith(("select", "with"))]
    if not main:
        raise ValueError("query has no SELECT statement")
    return [s for s in stmts if s is not main[-1]], main[-1]


# -----------------------------------------------------------------------------
# Clusters
# -----------------------------------------------------------------------------
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class StandaloneCluster:
    """One master + N identical workers on localhost, started with the pip-installed Spark."""

    def __init__(self, num_workers: int, worker_cores: int, worker_memory_mb: int, log_dir: Path):
        self.num_workers, self.worker_cores, self.worker_memory_mb = num_workers, worker_cores, worker_memory_mb
        self.log_dir = log_dir
        self.procs: List[subprocess.Popen] = []
        self.url = ""
        self.ui_url = ""

    def __enter__(self):
        spark_home = os.path.dirname(pyspark.__file__)
        env = dict(os.environ, SPARK_HOME=spark_home, SPARK_LOCAL_IP="127.0.0.1")
        spark_class = os.path.join(spark_home, "bin", "spark-class")
        port, ui_port = _free_port(), _free_port()
        self.url, self.ui_url = f"spark://127.0.0.1:{port}", f"http://127.0.0.1:{ui_port}"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.procs.append(subprocess.Popen(
            [spark_class, "org.apache.spark.deploy.master.Master", "--host", "127.0.0.1",
             "--port", str(port), "--webui-port", str(ui_port)],
            env=env, stdout=open(self.log_dir / "master.log", "w"), stderr=subprocess.STDOUT))
        self._wait_port(port)
        for i in range(self.num_workers):
            self.procs.append(subprocess.Popen(
                [spark_class, "org.apache.spark.deploy.worker.Worker", self.url,
                 "-c", str(self.worker_cores), "-m", f"{self.worker_memory_mb}m",
                 "--webui-port", str(_free_port()), "--work-dir", str(self.log_dir / f"work{i}")],
                env=env, stdout=open(self.log_dir / f"worker{i}.log", "w"), stderr=subprocess.STDOUT))
        self.wait_idle(expect_workers=self.num_workers)
        return self

    @staticmethod
    def _wait_port(port: int, timeout: float = 60.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return
            time.sleep(0.5)
        raise RuntimeError("Spark master did not start; see master.log")

    def state(self) -> Dict[str, Any]:
        with urllib.request.urlopen(f"{self.ui_url}/json/", timeout=10) as r:
            return json.load(r)

    def alive_workers(self) -> List[Dict[str, Any]]:
        return [w for w in self.state().get("workers", []) if w.get("state") == "ALIVE"]

    def wait_idle(self, expect_workers: int = 1, timeout: float = 120.0) -> None:
        """Block until the workers are registered and hold nothing from earlier apps."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                st = self.state()
                alive = [w for w in st.get("workers", []) if w.get("state") == "ALIVE"]
                if len(alive) >= expect_workers and not st.get("activeapps") and all(
                        w.get("coresused", 0) == 0 and w.get("memoryused", 0) == 0 for w in alive):
                    return
            except Exception:
                pass
            time.sleep(1.0)
        raise RuntimeError("standalone workers did not become idle; see cluster_logs")

    def __exit__(self, *exc):
        for p in reversed(self.procs):
            p.terminate()
        for p in self.procs:
            try:
                p.wait(timeout=20)
            except subprocess.TimeoutExpired:
                p.kill()


class ExternalCluster(StandaloneCluster):
    """An already-running standalone cluster (e.g. person-a-cluster/docker). Data must be
    mounted at the same absolute path on this driver and on every worker."""

    def __init__(self, url: str, ui_url: str):
        super().__init__(0, 0, 0, Path("."))
        self.url, self.ui_url = url, ui_url.rstrip("/")

    def __enter__(self):
        if not self.alive_workers():
            raise RuntimeError(f"no ALIVE workers at {self.ui_url}")
        self.wait_idle()
        return self

    def __exit__(self, *exc):
        pass


DRIVER_HOST: Optional[str] = None


def start_session(cluster_url: str, pool: Pool, dynamic: bool, driver_memory: str) -> SparkSession:
    n = pool.num_workers
    b = (SparkSession.builder.master(cluster_url).appName("prism-honest-benchmark")
         .config("spark.driver.memory", driver_memory)
         .config("spark.executor.cores", str(pool.executor_cores))
         .config("spark.executor.memory", f"{pool.executor_memory_mb}m")
         .config("spark.sql.adaptive.enabled", "true")
         .config("spark.ui.port", str(_free_port()))
         .config("spark.ui.showConsoleProgress", "false")
         # every allocation key is set explicitly: PySpark copies spark.* settings of a
         # stopped SparkContext into the next one, so anything left unset leaks.
         .config("spark.cores.max", str(n * pool.executor_cores))
         .config("spark.dynamicAllocation.enabled", str(dynamic).lower())
         .config("spark.dynamicAllocation.shuffleTracking.enabled", str(dynamic).lower())
         .config("spark.dynamicAllocation.shuffleTracking.timeout", "10s")
         .config("spark.dynamicAllocation.executorIdleTimeout", "10s")
         .config("spark.dynamicAllocation.minExecutors", "1")
         .config("spark.dynamicAllocation.initialExecutors", "1")
         .config("spark.dynamicAllocation.maxExecutors", str(n))
         .config("spark.scheduler.minRegisteredResourcesRatio", "0.0" if dynamic else "1.0")
         .config("spark.scheduler.maxRegisteredResourcesWaitingTime", "60s"))
    if DRIVER_HOST:
        b = b.config("spark.driver.host", DRIVER_HOST).config("spark.driver.bindAddress", "0.0.0.0")
    else:
        b = b.config("spark.driver.host", "127.0.0.1").config("spark.driver.bindAddress", "127.0.0.1")
    spark = b.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    _wait_executors(spark, lambda k: k >= 1, 90, "no executor registered")
    return spark


# -----------------------------------------------------------------------------
# Executor pool control and measurement
# -----------------------------------------------------------------------------
def _rest(spark: SparkSession, path: str) -> Any:
    sc = spark.sparkContext
    with urllib.request.urlopen(f"{sc.uiWebUrl}/api/v1/applications/{sc.applicationId}/{path}", timeout=30) as r:
        return json.load(r)


def active_executors(spark: SparkSession) -> List[str]:
    return sorted((e["id"] for e in _rest(spark, "executors") if e["id"] != "driver" and e.get("isActive", True)),
                  key=lambda x: int(x))


def _wait_executors(spark: SparkSession, ok, timeout: float, what: str) -> int:
    deadline = time.time() + timeout
    k = -1
    while time.time() < deadline:
        try:
            k = len(active_executors(spark))
            if ok(k):
                return k
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"{what} (have {k}) within {timeout:.0f} s")


def request_total(spark: SparkSession, n: int) -> None:
    sc = spark.sparkContext
    empty = sc._jvm.PythonUtils.toScalaMap(sc._jvm.java.util.HashMap())
    sc._jsc.sc().requestTotalExecutors(int(n), 0, empty)


def set_pool(spark: SparkSession, n: int, timeout: float = 120.0) -> None:
    """Resize the fixed-shape pool to exactly n registered executors."""
    jsc = spark.sparkContext._jsc.sc()
    deadline = time.time() + timeout
    request_total(spark, n)
    stable_since = None
    k = -1
    while time.time() < deadline:
        try:
            alive = active_executors(spark)
        except Exception:
            time.sleep(0.5)
            continue
        k = len(alive)
        if k > n:       # also kills an executor that registered late (e.g. requested by Stage 2 just before the
            stable_since = None   # previous query ended and not yet visible when the pool was first inspected)
            for eid in alive[n:][::-1]:
                jsc.killExecutor(eid)
        elif k < n:
            stable_since = None
            request_total(spark, n)
        else:           # exactly n: confirm it stays so for 1.5 s, so a late registration cannot slip in
            stable_since = stable_since or time.time()
            if time.time() - stable_since >= 1.5:
                return
        time.sleep(0.5)
    raise RuntimeError(f"pool did not reach {n} executors (have {k}) within {timeout:.0f} s")


def _parse_ts(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    return dt.datetime.strptime(s.replace("GMT", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()


def executor_usage(spark: SparkSession, t0: float, t1: float, mem_mb: int) -> Dict[str, float]:
    """Core-seconds and GB-seconds held by executors during [t0, t1], from the executor timeline."""
    core_s = mem_gb_s = 0.0
    live = set()
    for e in _rest(spark, "allexecutors"):
        if e["id"] == "driver":
            continue
        start = _parse_ts(e.get("addTime")) or t0
        end = _parse_ts(e.get("removeTime")) or t1
        overlap = max(0.0, min(end, t1) - max(start, t0))
        if overlap > 0:
            live.add(e["id"])
        core_s += overlap * e.get("totalCores", 0)
        mem_gb_s += overlap * mem_mb / 1024.0
    return {"alloc_core_s": core_s, "alloc_mem_gb_s": mem_gb_s, "executors_seen": len(live)}


def group_stages(spark: SparkSession, group: str) -> List[Dict[str, Any]]:
    stage_ids = set()
    for j in _rest(spark, "jobs"):
        if j.get("jobGroup") == group:
            stage_ids.update(j.get("stageIds", []))
    return [s for s in _rest(spark, "stages") if s["stageId"] in stage_ids]


def job_group_cpu(spark: SparkSession, group: str) -> Dict[str, float]:
    st = group_stages(spark, group)
    # What the live Stage 2 monitor sees: shuffle bytes of the stages complete at the moment the
    # first shuffle-map stage completes (same quantity for training and for inference).
    writers = [(_parse_ts(s.get("completionTime")), s) for s in st
               if s.get("status") == "COMPLETE" and s.get("shuffleWriteBytes", 0) > 0]
    writers = [(t, s) for t, s in writers if t is not None]
    ckpt_bytes, ckpt_parts = 0.0, 0
    if writers:
        first = min(t for t, _ in writers)
        ckpt_bytes = float(sum(s["shuffleWriteBytes"] for t, s in writers if t <= first + 0.25))
        later = [s for s in st if (_parse_ts(s.get("submissionTime")) or 0) > first]
        ckpt_parts = int(max((s.get("numTasks", 0) for s in later), default=0))
    return {"executor_cpu_s": sum(s.get("executorCpuTime", 0) for s in st) / 1e9,
            "executor_task_s": sum(s.get("executorRunTime", 0) for s in st) / 1e3,
            "shuffle_write_bytes": sum(s.get("shuffleWriteBytes", 0) for s in st),
            "checkpoint_shuffle_bytes": ckpt_bytes, "checkpoint_partitions": ckpt_parts}


def result_checksum(rows) -> str:
    def norm(v):
        if isinstance(v, float):
            return f"{v:.4f}"
        return str(v)
    lines = sorted("|".join(norm(v) for v in r) for r in rows)
    return hashlib.sha1("\n".join(lines).encode()).hexdigest()[:16]


class Stage2Monitor(threading.Thread):
    """Live Stage 2: at the first completed shuffle-map stage of the query, feed the real
    shuffle bytes / partition count to the Stage 2 model and grow the pool if it asks for more."""

    def __init__(self, spark, group, fv, bundle, pool: Pool, current: int, t0: float, fixed_target=None):
        super().__init__(daemon=True)
        self.fixed_target = fixed_target
        self.spark, self.group, self.fv, self.bundle = spark, group, fv, bundle
        self.pool, self.current, self.t0 = pool, current, t0
        self.stop_evt = threading.Event()
        self.info: Dict[str, Any] = {"stage2_fired": False}

    def run(self):
        while not self.stop_evt.wait(0.25):
            try:
                st = group_stages(self.spark, self.group)
            except Exception:
                continue
            done = [s for s in st if s.get("status") == "COMPLETE" and s.get("shuffleWriteBytes", 0) > 0]
            if not done:
                continue
            true_bytes = float(sum(s["shuffleWriteBytes"] for s in done))
            active = [s for s in st if s.get("status") == "ACTIVE"]
            parts = int(max((s.get("numTasks", 0) for s in active), default=0)) or \
                int(self.spark.conf.get("spark.sql.shuffle.partitions"))
            if self.fixed_target is not None:     # growth path: the target is given, no model
                e, c, m = self.fixed_target, self.pool.executor_cores, self.pool.executor_memory_mb
                target = self.fixed_target
            else:
                fv2 = extract_aqe_features(self.fv, true_bytes, parts)
                e, c, m = predict(self.bundle, fv2)
                target, _ = calibrated_count(e, c, m, self.pool)
            applied = target > self.current
            if applied:
                request_total(self.spark, target)
            self.info.update(stage2_fired=True, stage2_at_s=round(time.time() - self.t0, 3),
                             stage2_true_shuffle_bytes=true_bytes, stage2_partitions=parts,
                             stage2_raw_prediction=f"{e}x{c}x{m}", stage2_target=target,
                             stage2_applied=applied,
                             stage2_note="" if applied or target == self.current
                             else "shrink not applied mid-query")
            return


def run_once(spark: SparkSession, prelude: List[str], main_sql: str, sql_conf: Dict[str, str],
             timeout_s: float, mem_mb: int, group: str, stage2: Optional[Dict[str, Any]] = None,
             save_result: Optional[Path] = None) -> Dict[str, Any]:
    sc = spark.sparkContext
    for k, v in sql_conf.items():
        spark.conf.set(k, v)
    sc.setJobGroup(group, group, interruptOnCancel=True)
    timed_out = threading.Event()

    def _cancel():
        timed_out.set()
        sc.cancelJobGroup(group)

    timer = threading.Timer(timeout_s, _cancel)
    rec: Dict[str, Any] = {"status": "SUCCESS", "error": ""}
    try:
        rec["executors_at_start"] = len(active_executors(spark))
    except Exception:
        rec["executors_at_start"] = -1
    t0 = time.time()
    mon = None
    if stage2:
        mon = Stage2Monitor(spark, group, stage2["fv"], stage2["bundle"], stage2["pool"],
                            rec["executors_at_start"], t0, stage2.get("fixed_target"))
        mon.start()
    timer.start()
    try:
        for stmt in prelude:
            spark.sql(stmt)
        rows = spark.sql(main_sql).collect()
        t1 = time.time()
        rec.update(latency_s=t1 - t0, rows=len(rows), checksum=result_checksum(rows))
        if save_result is not None and not save_result.exists():
            save_result.parent.mkdir(parents=True, exist_ok=True)
            cols = rows[0].__fields__ if rows else []
            pd.DataFrame([list(r) for r in rows], columns=cols).to_csv(save_result, index=False)
    except Exception as e:
        t1 = time.time()
        rec.update(status="TIMEOUT" if timed_out.is_set() else "ERROR",
                   error=str(e).strip().split("\n")[0][:300], latency_s=float("nan"),
                   rows=-1, checksum="")
    finally:
        timer.cancel()
        if mon:
            mon.stop_evt.set()
            mon.join(timeout=5)
            rec.update(mon.info)
        for k in sql_conf:
            spark.conf.unset(k)
    rec["wall_s"] = t1 - t0
    try:
        rec.update(executor_usage(spark, t0, t1, mem_mb))
        rec.update(job_group_cpu(spark, group))
    except Exception as e:
        rec["metrics_error"] = str(e)[:200]
    return rec


def plan_only(args) -> None:
    spark = (SparkSession.builder.master("local[1]").appName("prism-plan-only")
             .config("spark.ui.enabled", "false").config("spark.driver.memory", "1g")
             .config("spark.sql.adaptive.enabled", "true").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    register_views(spark, args.benchmark, args.data_dir)
    query_dir = args.query_dir or PROJECT_ROOT / "workload" / f"{args.benchmark}-queries"
    rows = []
    for q in sorted(query_dir.glob("*.sql")):
        sql = sanitize_spark_sql(q.read_text())
        prelude, main_sql = split_statements(sql)
        for stmt in prelude:
            spark.sql(stmt)
        fv = extract_submission_features(spark.sql(main_sql), spark, query_id=q.stem, raw_sql=sql,
                                         data_dir=args.data_dir)
        rows.append({"query": q.stem, **fv.plan_features.model_dump()})
    spark.stop()
    args.plan_only.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.plan_only / "plan_features.csv", index=False)
    print(f"plan features -> {args.plan_only / 'plan_features.csv'}")


def prewarm_page_cache(data_dir: Path) -> None:
    t0, total = time.time(), 0
    for f in sorted(Path(data_dir).rglob("*")):
        if f.is_file():
            with open(f, "rb") as fh:
                while chunk := fh.read(1 << 24):
                    total += len(chunk)
    print(f"[prewarm] read {total / 1e9:.2f} GB in {time.time() - t0:.0f}s")


def _burn(stop):
    x = 0
    while not stop.is_set():
        for i in range(100000):
            x ^= i


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--benchmark", choices=["tpch", "tpcds"], required=True)
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--query-dir", type=Path)
    ap.add_argument("--queries", help="comma-separated subset, e.g. q1,q3")
    ap.add_argument("--strategies", default=",".join(STRATEGIES))
    ap.add_argument("--sweep", action="store_true",
                    help="run every executor count 1..N plus spark_dra (oracle + training data)")
    ap.add_argument("--reps", type=int, default=3, help="timed repetitions after one discarded warm-up")
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--num-workers", type=int, default=4, help="workers = maximum executors")
    ap.add_argument("--executor-cores", type=int, default=2)
    ap.add_argument("--executor-memory-mb", type=int, default=1536)
    ap.add_argument("--driver-memory", default="2g")
    ap.add_argument("--contention", type=int, default=0, help="K CPU-burner processes during the run")
    ap.add_argument("--calibration", choices=["original", "v2", "v3", "supply"], default="original",
                    help="v2: no capacity margin on an idle cluster (original caps at int(0.9 x N))")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--master", help="use an existing standalone master (spark://host:7077); its ALIVE "
                                     "workers must each fit one executor of the configured shape")
    ap.add_argument("--master-ui", default="http://localhost:8080")
    ap.add_argument("--driver-host", help="address executors use to reach this driver (external clusters)")
    ap.add_argument("--block-order", action="store_true",
                    help="training sweeps: group units by executor count, warm-up once per block "
                         "(use with --reps 1); data files are read once first to warm the page cache")
    ap.add_argument("--resume", action="store_true", help="reuse complete units from an existing runs.csv")
    ap.add_argument("--deadline", help="'YYYY-MM-DD HH:MM' local time: start no new unit after it")
    ap.add_argument("--plan-only", type=Path, metavar="SWEEP_DIR",
                    help="only recompute plan features (local[1], nothing executed) into SWEEP_DIR/plan_features.csv")
    ap.add_argument("--models-dir", type=Path, default=PROJECT_ROOT / "prism" / "model" / "baseline_models")
    ap.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "runs" / "benchmark")
    args = ap.parse_args(argv)

    global DRIVER_HOST
    DRIVER_HOST = args.driver_host
    if args.plan_only:
        return plan_only(args)
    if args.master:
        cluster_cm = ExternalCluster(args.master, args.master_ui)
        workers = cluster_cm.alive_workers()
        fit = [w for w in workers if w["cores"] >= args.executor_cores and w["memory"] >= args.executor_memory_mb]
        pool = Pool(len(fit), args.executor_cores, args.executor_memory_mb, args.contention, args.calibration)
    else:
        pool = Pool(args.num_workers, args.executor_cores, args.executor_memory_mb, args.contention, args.calibration)

    query_dir = args.query_dir or PROJECT_ROOT / "workload" / f"{args.benchmark}-queries"
    qfiles = sorted(query_dir.glob("*.sql"), key=lambda p: int("".join(filter(str.isdigit, p.stem)) or 0))
    if args.queries:
        wanted = set(args.queries.split(","))
        qfiles = [q for q in qfiles if q.stem in wanted]
    strategies = args.strategies.split(",")
    if args.sweep:
        strategies = [f"fixed_{k}e" for k in range(1, pool.num_workers + 1)] + ["spark_dra"]
    tag = f"{args.benchmark}_{args.data_dir.name}{'_sweep' if args.sweep else ''}_k{args.contention}_s{args.seed}"
    out_dir = args.out_dir / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    if not args.master:
        cluster_cm = StandaloneCluster(pool.num_workers, pool.executor_cores,
                                       pool.executor_memory_mb + 128, out_dir / "cluster_logs")

    bundles = load_bundles(args.models_dir)
    dispatcher = PluggableEnhancedDispatcher()

    stop_burn = mp.Event()
    burners = [mp.Process(target=_burn, args=(stop_burn,), daemon=True) for _ in range(args.contention)]
    for p in burners:
        p.start()

    records: List[Dict[str, Any]] = []
    raw_path = out_dir / "runs.csv"
    done: set = set()
    if args.resume and raw_path.exists():
        # keep only successful runs; every other unit (failed, timed out, interrupted) is rerun
        prev = pd.read_csv(raw_path)
        prev.to_csv(out_dir / f"runs.before_resume_{time.strftime('%H%M%S')}.csv", index=False)
        keep = prev[prev["status"] == "SUCCESS"]
        cnt = keep.groupby(["query", "strategy"]).size()
        done = {k for k, v in cnt.items() if v >= args.reps}
        keep = keep[[(q, st) in done for q, st in zip(keep["query"], keep["strategy"])]]
        records = keep.to_dict("records")
        print(f"[resume] keeping {len(records)} runs ({len(done)} complete (query, strategy) pairs); "
              f"discarded {len(prev) - len(records)} incomplete/failed rows")

    def record(unit_strats, qid, dec: Decision, rep: int, r: Dict[str, Any]):
        for s in unit_strats:
            records.append({"benchmark": args.benchmark, "dataset": args.data_dir.name, "query": qid,
                            "strategy": s, "rep": rep, "contention_k": args.contention, "seed": args.seed,
                            "requested_executors": dec.num_executors, "requested_cores": pool.executor_cores,
                            "requested_memory_mb": pool.executor_memory_mb, "dynamic": dec.dynamic,
                            "two_stage": bool(dec.two_stage_model),
                            "sql_conf": json.dumps(dec.sql_conf, sort_keys=True),
                            "shared_with": ",".join(x for x in unit_strats if x != s), **r})
        pd.DataFrame(records).to_csv(raw_path, index=False)

    deadline = time.mktime(time.strptime(args.deadline, "%Y-%m-%d %H:%M")) if args.deadline else None
    skipped: List[str] = []

    def past_deadline(key) -> bool:
        if deadline and time.time() > deadline:
            skipped.append(f"{key[0]}:n={key[1]}{':dra' if key[2] else ''}{':' + key[3] if key[3] else ''}")
            return True
        return False

    def run_unit(spark, key, us, label, prepare, warm=True):
        qid, prelude, main_sql, fv = us[0][0], us[0][2], us[0][3], us[0][4]
        dec: Decision = us[0][5]
        names = [u[1] for u in us]
        if all((qid, n) in done for n in names):
            print(f"  [resume] {qid} {','.join(names)} already measured")
            return
        stage2 = None
        if dec.two_stage_model.startswith("__grow"):
            stage2 = {"fv": fv, "bundle": None, "pool": pool, "fixed_target": int(dec.two_stage_model[len("__grow"):])}
        elif dec.two_stage_model:
            b2 = bundles[dec.two_stage_model]["stage2"]
            stage2 = {"fv": fv, "bundle": b2, "pool": pool} if b2 is not None else None
        for rep in range(0 if warm else 1, args.reps + 1):
            try:
                prepare(dec)
            except RuntimeError as e:
                print(f"  {qid} {label}: pool setup failed: {e}")
                record(names, qid, dec, rep, {"status": "POOL_ERROR", "error": str(e), "latency_s": float("nan")})
                return
            gid = f"{qid}-{label}-r{rep}-{rng.randrange(1 << 30)}"
            r = run_once(spark, prelude, main_sql, dec.sql_conf, args.timeout,
                         pool.executor_memory_mb, gid, stage2, save_result=out_dir / "results" / f"{qid}.csv")
            tag_ = "warm-up" if rep == 0 else f"rep {rep}"
            s2 = f" stage2->{r.get('stage2_target')}{'*' if r.get('stage2_applied') else ''}" \
                if r.get("stage2_fired") else ""
            print(f"  {tag_:7s} {qid:5s} n={dec.num_executors}{' DRA' if dec.dynamic else ''} "
                  f"{r['status']:7s} {r['wall_s']:7.2f}s seen={r.get('executors_seen')}{s2} [{','.join(names)}]")
            if rep > 0:
                record(names, qid, dec, rep, r)
            elif r["status"] == "TIMEOUT":
                # A configuration slower than the timeout stays slower; don't spend reps x timeout on it.
                for k in range(1, args.reps + 1):
                    record(names, qid, dec, k, {**r, "error": "warm-up exceeded timeout; reps skipped"})
                return

    try:
        with cluster_cm as cluster:
            spark = start_session(cluster.url, pool, False, args.driver_memory)
            try:
                register_views(spark, args.benchmark, args.data_dir)
                # ---- Phase 1: plan every strategy from the real Catalyst plan ----
                decisions, units = [], {}
                cl = pool.calibration_capacity()
                for q in qfiles:
                    sql = sanitize_spark_sql(q.read_text())
                    try:
                        prelude, main_sql = split_statements(sql)
                        for stmt in prelude:
                            spark.sql(stmt)
                        fv = extract_submission_features(spark.sql(main_sql), spark, query_id=q.stem,
                                                         raw_sql=sql, data_dir=args.data_dir)
                    except Exception as e:
                        print(f"[plan] {q.stem}: planning failed: {str(e).splitlines()[0][:200]}")
                        decisions.append({"query": q.stem, "strategy": "*", "status": "PLAN_ERROR",
                                          "error": str(e)[:300]})
                        continue
                    fv.cluster_load_features.queue_depth = 0
                    fv.cluster_load_features.available_executors = cl.available_executors
                    fv.cluster_load_features.available_cores = cl.available_cores
                    fv.cluster_load_features.colocated_job_count = args.contention
                    for strat in strategies:
                        dec, meta = decide(strat, fv, sql, bundles, dispatcher, pool)
                        decisions.append({"query": q.stem, "strategy": strat, **asdict(dec), **meta,
                                          "input_size_bytes": fv.plan_features.input_size_bytes,
                                          "join_order_depth": fv.plan_features.join_order_depth,
                                          "estimated_shuffle_bytes": fv.plan_features.estimated_shuffle_bytes,
                                          "stage_dag_depth": fv.plan_features.stage_dag_depth,
                                          "stage_dag_branch_factor": fv.plan_features.stage_dag_branch_factor,
                                          "join_type": fv.plan_features.join_type})
                        # Strategies with identical decisions share runs (recorded in shared_with).
                        key = (q.stem, dec.num_executors, dec.dynamic, strat if dec.two_stage_model else "", tuple(sorted(dec.sql_conf.items())))
                        units.setdefault(key, []).append((q.stem, strat, prelude, main_sql, fv, dec))
                pd.DataFrame(decisions).to_csv(out_dir / "decisions.csv", index=False)

                # ---- Phase 2a: fixed-shape pool, resized per unit ----
                fixed = [k for k in units if not k[2]]
                rng.shuffle(fixed)
                first_in_block = set()
                if args.block_order:
                    # training mode: all units at one executor count, then the next count (4,1,3,2);
                    # the pool stays warm inside a block, so only the block's first unit gets a warm-up
                    order = [pool.num_workers, 1] + [n for n in range(pool.num_workers - 1, 1, -1)]
                    fixed.sort(key=lambda k: order.index(k[1]) if k[1] in order else len(order))
                    prev = None
                    for k in fixed:
                        if k[1] != prev:
                            first_in_block.add(k)
                            prev = k[1]
                    prewarm_page_cache(args.data_dir)
                for i, key in enumerate(fixed, 1):
                    if past_deadline(key):
                        continue
                    print(f"[{i}/{len(fixed)}] {key[0]} n={key[1]} {key[3] or ''}")
                    run_unit(spark, key, units[key], f"u{i}", lambda d: set_pool(spark, d.num_executors),
                             warm=(not args.block_order) or key in first_in_block)
            finally:
                spark.stop()

            # ---- Phase 2b: real dynamic allocation, reset to 1 executor before each run ----
            dra = [k for k in units if k[2]]
            if dra:
                cluster.wait_idle()
                spark = start_session(cluster.url, pool, True, args.driver_memory)
                try:
                    register_views(spark, args.benchmark, args.data_dir)
                    rng.shuffle(dra)
                    for i, key in enumerate(dra, 1):
                        if past_deadline(key):
                            continue
                        print(f"[DRA {i}/{len(dra)}] {key[0]}")
                        run_unit(spark, key, units[key], f"d{i}",
                                 lambda d: _wait_executors(spark, lambda k: k <= 1, 120,
                                                           "DRA pool did not shrink to 1"))
                finally:
                    spark.stop()
    finally:
        stop_burn.set()
        for p in burners:
            p.join(timeout=5)

    meta = {"benchmark": args.benchmark, "data_dir": str(args.data_dir), "reps": args.reps,
            "timeout_s": args.timeout, "num_workers": pool.num_workers,
            "executor_cores": pool.executor_cores, "executor_memory_mb": pool.executor_memory_mb,
            "contention_k": args.contention, "calibration": args.calibration, "models_dir": str(args.models_dir), "seed": args.seed,
            "master": args.master or "self-managed localhost", "block_order": args.block_order, "host_cpus": os.cpu_count(),
            "spark": pyspark.__version__, "python": sys.version.split()[0],
            "finished": time.strftime("%Y-%m-%d %H:%M:%S"), "deadline": args.deadline,
            "units_skipped_by_deadline": skipped}
    (out_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2))
    print(f"\nRaw runs: {raw_path}\nDecisions: {out_dir / 'decisions.csv'}")


if __name__ == "__main__":
    main()
