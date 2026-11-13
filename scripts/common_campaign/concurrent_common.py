# Isolated common-query extension of concurrent_benchmark.py, frozen 2026-10-26.
# Supports explicit workloads, strict success coverage, incremental evidence,
# one-tenant disk-backed references and owned-child cleanup. Original untouched.
"""
Concurrent query mixes: S tenants (separate Spark applications) share one standalone cluster of N executor slots.

Each tenant runs the explicitly selected TPC-H-derived queries in its own seeded order. Before each query its policy chooses an
executor count n; the tenant releases surplus executors at once, requests the rest, and waits up to --grant-wait
seconds for them (at least one executor is always awaited), then runs with what it holds. The response time of a
query is waiting time + execution time, i.e. what a tenant of a shared cluster experiences.

Policies and query populations are selected explicitly from configs/experiments.json.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import signal
import shutil
import subprocess
import tempfile
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

import prism.evaluation.honest_benchmark as hb
sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_extensions import SafeCluster, ObservedMonitor
from tenant_policies import TenantPolicies
CONCURRENT_POLICIES = tuple(json.loads((PROJECT_ROOT/'configs/experiments.json').read_text())['concurrent_policies'])
hb.StandaloneCluster = SafeCluster
hb.Stage2Monitor = ObservedMonitor
from prism.evaluation.multi_classifier_benchmark import sanitize_spark_sql

N_SLOTS, EXEC_CORES, EXEC_MEM = 4, 2, 1536


def master_state(ui):
    with urllib.request.urlopen(f"{ui}/json/", timeout=10) as r:
        return json.load(r)


def session(url, dynamic, driver_mem):
    from pyspark.sql import SparkSession
    b = (SparkSession.builder.master(url).appName("prism-concurrent")
         .config("spark.driver.memory", driver_mem)
         .config("spark.executor.cores", str(EXEC_CORES)).config("spark.executor.memory", f"{EXEC_MEM}m")
         .config("spark.sql.adaptive.enabled", "true").config("spark.ui.port", str(hb._free_port()))
         .config("spark.ui.showConsoleProgress", "false").config("spark.cores.max", str(N_SLOTS * EXEC_CORES))
         .config("spark.dynamicAllocation.enabled", str(dynamic).lower())
         .config("spark.dynamicAllocation.shuffleTracking.enabled", str(dynamic).lower())
         .config("spark.dynamicAllocation.shuffleTracking.timeout", "10s")
         .config("spark.dynamicAllocation.executorIdleTimeout", "10s")
         .config("spark.dynamicAllocation.minExecutors", "1").config("spark.dynamicAllocation.initialExecutors", "1")
         .config("spark.dynamicAllocation.maxExecutors", str(N_SLOTS))
         .config("spark.scheduler.minRegisteredResourcesRatio", "0.0")
         .config("spark.driver.host", "127.0.0.1").config("spark.driver.bindAddress", "127.0.0.1"))
    spark = b.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def shrink_to(spark, n):
    alive = hb.active_executors(spark)
    jsc = spark.sparkContext._jsc.sc()
    for eid in alive[n:][::-1]:
        jsc.killExecutor(eid)
    hb.request_total(spark, n)


def wait_for_allocation(spark, requested, grant_wait, timeout):
    """Never launch above the policy target; bounded under-grant is permitted."""
    started = time.monotonic()
    hb.request_total(spark, requested)
    stable_since = None
    stable_count = None
    while True:
        count = len(hb.active_executors(spark))
        elapsed = time.monotonic() - started
        if count == requested or (0 < count < requested and elapsed >= grant_wait):
            if stable_count != count:
                stable_count, stable_since = count, time.monotonic()
            if time.monotonic() - stable_since >= 1.5:
                return count
        else:
            stable_count, stable_since = None, None
        if elapsed >= timeout:
            raise RuntimeError(f"Executor allocation did not settle at <= {requested} before timeout (have {count})")
        if count > requested:
            # killExecutor is asynchronous and may also adjust the requested total.
            # Observe the release before execution and reassert the desired target.
            shrink_to(spark, requested)
        time.sleep(0.25)


def archive_attempt(directory, tag, outputs):
    """Remove stale active files only by moving them to an evidence archive."""
    paths = [p for p in outputs if p.exists()]
    paths += [p for p in (directory / "runs.csv", directory / "run_metadata.json",
                         directory / "cluster_logs" / tag) if p.exists()]
    if not paths:
        return
    archive = directory / "attempts" / f"{tag}_{time.time_ns()}"
    archive.mkdir(parents=True, exist_ok=False)
    for path in paths:
        destination = archive / path.relative_to(directory)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))


def free_for_me(ui, app_id):
    """Executor slots this tenant could hold: all slots minus those held by the other tenants."""
    st = master_state(ui)
    others = sum(a.get("cores", 0) for a in st.get("activeapps", []) if a.get("id") != app_id)
    return max(1, N_SLOTS - others // EXEC_CORES)


def tenant_barrier(directory, stream_id, streams, app_id, timeout=600):
    """Persist readiness so a quick tenant cannot disappear from a peer's barrier.

    The parent supplies a fresh private directory for each physical mix attempt.
    Each caller first confirms its own executor allocation. Arrival records stay
    until the parent joins all children, including tenants that already finished.
    """
    directory = Path(directory)
    if not 0 <= stream_id < streams:
        raise ValueError("Invalid tenant barrier identity")
    marker = directory / f"tenant-{stream_id}.ready"
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(app_id + "\n")
    temporary.replace(marker)
    deadline = time.monotonic() + timeout
    expected = [directory / f"tenant-{i}.ready" for i in range(streams)]
    while not all(path.is_file() for path in expected):
        if time.monotonic() >= deadline:
            missing = [path.name for path in expected if not path.is_file()]
            raise RuntimeError(f"Tenant readiness barrier timed out: {missing}")
        time.sleep(0.25)


def stream(args):
    rng = random.Random(1000 * args.rep + args.stream)
    qfiles = sorted(Path(args.query_dir).glob("*.sql"), key=lambda p: p.stem)
    if args.queries:
        wanted = set(args.queries.split(","))
        qfiles = [q for q in qfiles if q.stem in wanted]
    if not qfiles:
        raise RuntimeError("Empty concurrent workload")
    rng.shuffle(qfiles)
    dynamic = args.policy == "spark_dra"
    spark = session(args.master, dynamic, args.driver_memory)
    app = spark.sparkContext.applicationId
    hb.register_views(spark, "tpch", Path(args.data_dir))
    plans = {}
    policies = TenantPolicies(args.policy, args.models_dir, args.base_models_dir, args.profiles_dir)
    need_features = not (args.policy.startswith("static_") or dynamic)
    for q in qfiles:
        sql = sanitize_spark_sql(q.read_text())
        prelude, main_sql = hb.split_statements(sql)
        for s in prelude:
            spark.sql(s)
        fv = hb.extract_submission_features(spark.sql(main_sql), spark, query_id=q.stem, raw_sql=sql,
                                            data_dir=Path(args.data_dir)) if need_features else None
        plans[q.stem] = (prelude, main_sql, fv, sql)
    if not dynamic:
        # Wait for late executor registrations and release excess startup slots
        # before announcing readiness; a single kill pass is asynchronous.
        hb.set_pool(spark, 1, timeout=600)
    else:
        hb._wait_executors(spark, lambda n: n >= 1, 600,
                           "DRA tenant did not receive its initial executor")
    tenant_barrier(args.barrier_dir, args.stream, args.n_streams, app)
    time.sleep(2.0)
    rows = []
    for i, q in enumerate(qfiles):
        prelude, main_sql, fv, sql = plans[q.stem]
        t_req = time.time()
        available = free_for_me(args.ui, app)
        if fv is not None:
            fv.cluster_load_features.available_executors = available
            fv.cluster_load_features.available_cores = available * EXEC_CORES
            fv.cluster_load_features.colocated_job_count = args.n_streams - 1
        n, sql_conf, stage2, profile_meta = policies.choose(q.stem, sql, fv, available)
        raw = n
        if n is not None:
            wait_for_allocation(spark, n, args.grant_wait, args.timeout)
        wait_s = time.time() - t_req
        rec = hb.run_once(spark, prelude, main_sql, sql_conf, args.timeout, EXEC_MEM, f"c{args.stream}-{i}", stage2=stage2)
        rows.append({"policy": args.policy, "streams": args.n_streams, "rep": args.rep, "stream": args.stream,
                     "position": i, "query": q.stem, "raw_prediction": raw, "requested": n if n else -1,
                     "wait_s": wait_s, "response_s": wait_s + (rec.get("latency_s") or float("nan")),
                     "t_request": t_req, "policy_sql_conf": json.dumps(sql_conf), **profile_meta, **{k: v for k, v in rec.items() if not isinstance(v, (dict, list))}})
        pd.DataFrame(rows).to_csv(args.out, index=False)
        print(f"[{args.policy} S={args.n_streams} t{args.stream}] {i + 1:2d}/{len(qfiles)} {q.stem:4s} n={n} "
              f"start={rec.get('executors_at_start')} wait={wait_s:5.1f}s lat={rec.get('latency_s', float('nan')):6.1f}s "
              f"{rec['status']}", flush=True)
    spark.stop()
    pd.DataFrame(rows).to_csv(args.out, index=False)


def main():
    def terminate(signum,frame):
        raise KeyboardInterrupt('Owned concurrent measurement cancelled at campaign time boundary')
    signal.signal(signal.SIGTERM,terminate)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--query-dir", default=str(PROJECT_ROOT / "workload/tpch-queries"))
    ap.add_argument("--queries", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--streams", default="1,2,3")
    ap.add_argument("--policies", default=",".join(CONCURRENT_POLICIES))
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--grant-wait", type=float, default=60.0)
    ap.add_argument("--timeout", type=float, default=1200.0)
    ap.add_argument("--driver-memory", default="1g")
    ap.add_argument("--models-dir", default=str(PROJECT_ROOT / "prism/model/expanded_training"))
    ap.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "results/measurements/concurrent")
    ap.add_argument("--base-models-dir", default=str(PROJECT_ROOT / "prism/model/baseline_models"))
    ap.add_argument("--profiles-dir")
    # internal: one tenant
    ap.add_argument("--barrier-dir", type=Path)
    ap.add_argument("--stream", type=int)
    ap.add_argument("--n-streams", type=int)
    ap.add_argument("--policy")
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--master")
    ap.add_argument("--ui")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.stream is not None:
        if args.barrier_dir is None:
            ap.error("--barrier-dir is required for an internal tenant")
        return stream(args)

    wanted = {p.stem for p in Path(args.query_dir).glob("*.sql")}
    if args.queries:
        wanted &= set(args.queries.split(","))
    if not wanted:
        raise RuntimeError("Empty concurrent workload")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    meta = {"spark_local_dirs": "private disk-backed scratch, identical for dedicated references and mixes", "started": time.strftime("%F %T"), "args": {k: str(v) for k, v in vars(args).items()},
            "slots": N_SLOTS, "executor": f"{EXEC_CORES} cores x {EXEC_MEM} MB"}
    failed_mixes = []
    for rep in range(args.reps):
        for S in [int(x) for x in args.streams.split(",")]:
            for pol in args.policies.split(","):
                tag = f"{pol}_S{S}_r{rep}"
                outs = [args.out_dir / f"{tag}_t{i}.csv" for i in range(S)]
                if not args.force and all(o.exists() and len(pd.read_csv(o)) == len(wanted)
                       and set(pd.read_csv(o)["query"]) == wanted
                       and pd.read_csv(o).status.eq("SUCCESS").all() for o in outs):
                    print(f"[resume] {tag} done")
                    continue
                archive_attempt(args.out_dir, tag, outs)
                print(f"=== {time.strftime('%F %T')} mix {tag}", flush=True)
                t0 = time.time()
                # 2-3 tenants shuffle at the same time: the 7.7 GB in-memory /tmp would overflow, so executors spill to
                # disk here, including all matched single-tenant references.
                local = args.out_dir / "scratch" / tag
                local.mkdir(parents=True, exist_ok=True)
                os.environ["SPARK_LOCAL_DIRS"] = str(local)
                with tempfile.TemporaryDirectory(prefix="tenant-barrier-", dir=args.out_dir) as barrier_dir, hb.StandaloneCluster(N_SLOTS, EXEC_CORES, EXEC_MEM + 128, args.out_dir / "cluster_logs" / tag) as cl:
                    procs = [subprocess.Popen([sys.executable, "-I", "-u", __file__, "--data-dir", args.data_dir,
                                               "--barrier-dir", barrier_dir, "--stream", str(i), "--n-streams", str(S), "--policy", pol,
                                               "--rep", str(rep), "--master", cl.url, "--ui", cl.ui_url,
                                               "--out", str(outs[i]), "--grant-wait", str(args.grant_wait),
                                               "--timeout", str(args.timeout), "--driver-memory", args.driver_memory,
                                               "--models-dir", args.models_dir, "--query-dir", args.query_dir,
                                               "--queries", args.queries, "--base-models-dir", args.base_models_dir,
                                               *(["--profiles-dir", args.profiles_dir] if args.profiles_dir else [])], start_new_session=True)
                             for i in range(S)]
                    try:
                        codes = [p.wait(timeout=max(4 * 3600, len(wanted) * args.timeout * 2)) for p in procs]
                    finally:
                        for p in procs:
                            if p.poll() is None:
                                try:
                                    os.killpg(p.pid, signal.SIGTERM)
                                    p.wait(timeout=20)
                                except (ProcessLookupError, subprocess.TimeoutExpired):
                                    try:
                                        os.killpg(p.pid, signal.SIGKILL)
                                    except ProcessLookupError:
                                        pass
                print(f"    exit codes {codes}, makespan {time.time() - t0:.0f}s", flush=True)
                shutil.rmtree(local, ignore_errors=True)
                if any(code != 0 for code in codes):
                    failed_mixes.append({"mix": tag, "exit_codes": codes})
    frames = [pd.read_csv(f) for f in sorted(args.out_dir.glob("*_t*.csv"))]
    if frames:
        pd.concat(frames).to_csv(args.out_dir / "runs.csv", index=False)
    meta["failed_mixes"] = failed_mixes
    meta["finished"] = time.strftime("%F %T")
    (args.out_dir / "run_metadata.json").write_text(json.dumps(meta, indent=1))

    if failed_mixes:
        raise RuntimeError(f"Tenant subprocess failure: {failed_mixes}")


if __name__ == "__main__":
    main()
