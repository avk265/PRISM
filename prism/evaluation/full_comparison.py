"""
Complete PRISM vs baselines: every component combination, every metric, one execution protocol.

Every policy picks an executor count from the same pool (1..N executors, 2 cores x 1536 MB each, same
cluster). Every execution is scored with a run that was really measured at that count in the official
10 GB sweep, so no latency is modelled. Protocol (identical for all policies):

  stream  = R rounds over the test queries (round r uses repetition r of the measured runs), each round
            in a random order; S seeds (orders). Recurring queries are what feedback can learn from.
  SLA     = per query, fixed: SLA_FACTOR x median fixed_N latency (the static all-executors allocation).

PRISM components (all 2 x 2 x 4 combinations, for each model x {label, lm} predictor):
  S1   Stage 1: predictor on plan features before the query runs (always on)
  CAL  calibration: prism.calibration.calibrate() (caps at int(0.9 x available executors))
  S2   Stage 2: predictor + real shuffle bytes at the first shuffle checkpoint, grow-only
       (n = max(S1, S2)). A query whose count grows from a (Stage 1 count after drift/calibration) to b is
       scored with a run that really started on a executors and grew to b at the first completed
       shuffle-map stage (honest_benchmark.py grow_<a>to<b>, passed with --grow); without that run the
       comparison stops instead of approximating.
  FB   feedback after each delivered query: none | drift (prism/plugin/online_learning.py executor
       multiplier, as shipped) | retrain (refit the predictors on the training data + every delivered
       query, every RETRAIN_EVERY queries) | both
       retrain feedback rows: lm -> the observed (features, n, log latency); label -> pseudo-label
       n if the run met its SLA, else n+1 (only the chosen count is observed, as in production)

Baselines: fixed 1..N, heuristic, Spark DRA (measured runs), Lyu/RIOS rules (repo definitions),
Ernest and CherryPick (search runs counted as cost), original PRISM artifacts, oracle.

Outputs (--out): executions.csv, policy_metrics.csv, ablation.csv, learning_curve.csv, report.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from prism.model.train_from_sweep import (SLA_FACTOR, STAGE1_FEATURES, STAGE2_EXTRA, MODEL_TYPES, build_model,
                                          load_sweeps, build_table, _long, stage2_rows, lyu_rule, rios_rule,
                                          ernest_choice, cherrypick_choice, original_prism_choices,
                                          offline_tuned_static)
from prism.plugin.online_learning import OnlineDriftAdaptationPlugin, QueryTelemetryRecord
from prism.calibration.calibrate import calibrate
from prism.shared.schemas import CalibrationInput, ClusterCapacity

FEEDBACK_WEIGHT = 5.0   # weight of a delivered-query row vs a training row (fixed a priori, not tuned)
RETRAIN_EVERY = 11      # refit after every 11 delivered queries (twice per round of 22)
FB_MODES = ["none", "drift", "retrain", "both"]
JOBS = -1               # threads per model fit (--jobs)
_BASE_FITS = {}
DRIFT_Z, DRIFT_RATE = 1.645, 0.25   # online_learning.py defaults (--drift-z, --drift-rate)


def table_of(dirs):
    runs, decs, pf = load_sweeps(dirs)
    n = int(runs["strategy"].str.extract(r"fixed_(\d+)e")[0].dropna().astype(int).max())
    t, dropped = build_table(runs, decs, n, plan_feats=pf)
    return t, dropped, n, runs


def rep_lookup(runs):
    """{(query, n | 'dra', rep): (latency_s, core_h, cpu_h, mem_gbh)} from successful measured runs."""
    sel = runs["strategy"].str.match(r"^(fixed_\d+e|spark_dra)$")
    ok = runs[sel & runs["status"].isin(["SUCCESS", "TIMEOUT"])].copy()
    to = ok["status"] == "TIMEOUT"   # censored: scored at the time it ran before cancellation (a lower bound)
    ok.loc[to, "latency_s"] = ok.loc[to, "wall_s"]
    ok[["alloc_core_s", "executor_cpu_s", "alloc_mem_gb_s"]] = ok[["alloc_core_s", "executor_cpu_s", "alloc_mem_gb_s"]].fillna(0)
    ok["key"] = ok["strategy"].str.extract(r"fixed_(\d+)e")[0].astype(float)
    out = {}
    for r in ok.itertuples():
        k = "dra" if r.strategy == "spark_dra" else int(r.key)
        out[(r.query, k, int(r.rep))] = (r.latency_s, r.alloc_core_s / 3600, r.executor_cpu_s / 3600,
                                         r.alloc_mem_gb_s / 3600)
    return out


def grow_lookup(dirs):
    """{(query, a, b, rep): (latency_s, core_h, cpu_h, mem_gbh)} from measured growth-path runs grow_<a>to<b>."""
    out = {}
    for d in dirs or []:
        r = pd.read_csv(Path(d) / "runs.csv")
        r = r[r["strategy"].str.match(r"^grow_\d+to\d+$") & r["status"].isin(["SUCCESS", "TIMEOUT"])].copy()
        to = r["status"] == "TIMEOUT"
        r.loc[to, "latency_s"] = r.loc[to, "wall_s"]
        r[["alloc_core_s", "executor_cpu_s", "alloc_mem_gb_s"]] = r[["alloc_core_s", "executor_cpu_s", "alloc_mem_gb_s"]].fillna(0)
        for x in r.itertuples():
            a, b = (int(v) for v in x.strategy[len("grow_"):].split("to"))
            out[(x.query, a, b, int(x.rep))] = (x.latency_s, x.alloc_core_s / 3600, x.executor_cpu_s / 3600,
                                                x.alloc_mem_gb_s / 3600)
    return out


def calibration_cap(n_max, cores=2):
    out = calibrate(CalibrationInput(predicted_num_executors=n_max + 1, predicted_executor_cores=cores,
                                     predicted_executor_memory_mb=1536, confidence=0.9,
                                     cluster_load=ClusterCapacity(available_executors=n_max,
                                                                  available_cores=cores * n_max)))
    return out.calibrated.num_executors


class Learner:
    """One PRISM predictor (model kind x mode) for one stage; refit on training rows + feedback rows."""

    def __init__(self, kind, mode, cols, params, base, n_max, margin=0.0):
        self.kind, self.mode, self.cols, self.params, self.n_max = kind, mode, cols, params, n_max
        self.margin = margin   # safety margin tuned on the training queries (train_from_sweep.MARGINS)
        if mode == "label":
            self.X0, self.y0 = base[cols].to_numpy(float), base["label"].to_numpy(float)
        else:
            self.X0, self.y0 = _long(base, cols, n_max)
        key = (kind, mode, tuple(cols), len(base))
        if key not in _BASE_FITS:   # the fit on the training data alone is shared by every config and seed
            _BASE_FITS[key] = self.fit([]).model
        self.model = _BASE_FITS[key]

    def fit(self, fb):
        X, y = self.X0, self.y0
        w = np.ones(len(y))
        if fb:
            X = np.vstack([X, np.array([f[0] for f in fb], float)])
            y = np.concatenate([y, [f[1] for f in fb]])
            w = np.concatenate([w, np.full(len(fb), FEEDBACK_WEIGHT)])
        params = {**self.params, **({"n_jobs": JOBS} if self.kind in ("random_forest", "xgboost", "lightgbm") else {})}
        self.model = build_model(self.kind, params).fit(X, y, reg__sample_weight=w)
        return self

    def choose(self, F):
        F = np.atleast_2d(np.asarray(F, float))
        if self.mode == "label":
            return np.clip(np.round(self.model.predict(F) + self.margin), 1, self.n_max).astype(int)
        ns = np.arange(1, self.n_max + 1, dtype=float)
        grid = np.column_stack([np.repeat(F, len(ns), axis=0), np.tile(ns, len(F))])
        pred = self.model.predict(grid).reshape(len(F), len(ns))
        ok = pred <= pred.min(axis=1, keepdims=True) + np.log(SLA_FACTOR) - self.margin
        return (ok.argmax(axis=1) + 1).astype(int)

    def feedback_row(self, f, n, lat, met):
        if self.mode == "lm":
            return (list(f) + [float(n)], float(np.log(lat)))
        return (list(f), float(n if met else min(n + 1, self.n_max)))


def stream(test, R, seed):
    rng = np.random.default_rng(seed)
    return [(r, int(i)) for r in range(1, R + 1) for i in rng.permutation(test.index.to_numpy())]


def heuristic_n(row, n_max):
    return int(min(n_max, max(1, round(row["input_size_bytes"] / 1e9 * 2.5 + 1))))


def run_prism(test, train, tr2, s1c, s2c, specs, margins, kind, mode, cal, s2, fb, safe, seed, R, n_max, cap, reps,
              drift_baseline, fallback=False, ranges=None, grow=None):
    """Replays one complete-PRISM configuration over the stream; returns its executions."""
    m1, m2 = (margins.get(f"{kind}|{mode}|stage{i}", 0.0) if safe else 0.0 for i in (1, 2))
    L1 = Learner(kind, mode, s1c, specs[f"{kind}|{mode}|stage1"], train, n_max, m1)
    L2 = Learner(kind, mode, s2c, specs[f"{kind}|{mode}|stage2"], tr2, n_max, m2) if s2 else None
    drift = None
    if fb in ("drift", "both"):
        drift = OnlineDriftAdaptationPlugin(drift_z_threshold=DRIFT_Z, adaptation_rate=DRIFT_RATE)
        drift.initialize_baseline(drift_baseline)
    has2 = stage2_rows(test)
    fb1, fb2, rows = [], [], []
    for k, (r, i) in enumerate(stream(test, R, seed)):
        q = test.at[i, "query"]
        t0 = time.perf_counter()
        f1 = test.loc[i, s1c].to_numpy(float)
        n = int(L1.choose(f1)[0])
        # proposal Phase 5: novel query shape (any plan feature outside the training range) -> proportional heuristic
        ood = bool(fallback and any(not (lo <= v <= hi) for v, (lo, hi) in zip(f1, ranges)))
        if ood:
            n = heuristic_n(test.loc[i], n_max)
        n_stage1 = n
        if L2 is not None and has2[i] and not ood:
            n = max(n, int(L2.choose(test.loc[i, s2c].to_numpy(float))[0]))
        mult = 1.0
        n_start = n_stage1     # count the query starts with; Stage 2 can only grow it mid-query
        if drift is not None:
            n, _, mult = drift.adapt_recommendation(n, 1536)
            n = max(1, min(n_max, n))
            n_start = max(1, min(n_max, drift.adapt_recommendation(n_stage1, 1536)[0]))
        if cal:
            n = min(n, cap)
            n_start = min(n_start, cap)
        dt_ms = 1000 * (time.perf_counter() - t0)
        if n > n_start:        # real mid-query growth run
            if grow is None or (q, n_start, n, r) not in grow:
                raise KeyError(f"no measured growth run {q} {n_start}->{n} rep {r}: run honest_benchmark.py "
                               f"--strategies grow_{n_start}to{n} and pass it with --grow")
            lat, coreh, cpuh, memh = grow[(q, n_start, n, r)]
        else:
            lat, coreh, cpuh, memh = reps[(q, n, r)]
        met = lat <= test.at[i, "sla_target"]
        rows.append({"seed": seed, "round": r, "position": k, "query": q, "n": n, "n_stage1": n_stage1, "n_start": n_start, "fallback": ood, "latency_s": lat, "core_h": coreh,
                     "cpu_h": cpuh, "mem_gbh": memh, "decision_ms": dt_ms, "drift_multiplier": mult})
        if drift is not None:
            drift.record_telemetry(QueryTelemetryRecord(
                query_id=q, workload="tpch", timestamp=float(k), estimated_shuffle_bytes=test.at[i, "estimated_shuffle_bytes"],
                true_post_shuffle_bytes=float(np.nan_to_num(test.at[i, "true_post_shuffle_bytes"])),
                allocated_executors=n, allocated_cores=2, allocated_memory_mb=1536, measured_latency_s=lat,
                measured_cpu_waste_h=coreh - cpuh, measured_gc_ms=0.0, sla_target_s=test.at[i, "sla_target"],
                sla_met=bool(met)))
        if fb in ("retrain", "both"):
            fb1.append(L1.feedback_row(f1, n, lat, met))
            if L2 is not None and has2[i]:
                fb2.append(L2.feedback_row(test.loc[i, s2c].to_numpy(float), n, lat, met))
            if (k + 1) % RETRAIN_EVERY == 0:
                L1.fit(fb1)
                if L2 is not None:
                    L2.fit(fb2)
    return rows


def fixed_policy_rows(test, choice, R, reps, key=None, extra_core_h=0.0):
    """Executions of a policy whose choice does not depend on the order (same for every seed)."""
    rows = []
    for i in test.index:
        q = test.at[i, "query"]
        for r in range(1, R + 1):
            k = key or int(choice[i])
            lat, coreh, cpuh, memh = reps[(q, k, r)]
            rows.append({"seed": 0, "round": r, "position": np.nan, "query": q, "n": np.nan if key else k, "latency_s": lat,
                         "core_h": coreh, "cpu_h": cpuh, "mem_gbh": memh, "decision_ms": 0.0,
                         "drift_multiplier": 1.0})
    df = pd.DataFrame(rows)
    df["search_core_h"] = extra_core_h / len(df)
    return df


def bootstrap_ci(per_q: pd.Series, stat, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    v = per_q.to_numpy(float)
    b = [stat(v[rng.integers(0, len(v), len(v))]) for _ in range(n)]
    return np.percentile(b, [2.5, 97.5])


def metrics(ex: pd.DataFrame, test: pd.DataFrame, n_max: int) -> dict:
    t = test.set_index("query")
    ex = ex.assign(sla_target=ex["query"].map(t["sla_target"]), label=ex["query"].map(t["label"]),
                   static=ex["query"].map(t[f"lat_{n_max}"]),
                   oracle=ex["query"].map(t[[f"lat_{n}" for n in range(1, n_max + 1)]].min(axis=1)))
    ex["met"] = ex["latency_s"] <= ex["sla_target"]
    seeds = ex["seed"].nunique()
    per_seed = lambda col, f: float(ex.groupby("seed")[col].agg(f).mean())
    lat = ex["latency_s"]
    slow = lat / ex["static"]
    perq = ex.groupby("query").agg(met=("met", "mean"), core_h=("core_h", "sum"))
    search = float(ex["search_core_h"].sum()) / seeds if "search_core_h" in ex else 0.0
    core_h = per_seed("core_h", "sum")
    cpu_h = per_seed("cpu_h", "sum")
    m = {"executions": int(len(ex) / seeds), "seeds": seeds,
         "sla_pct": 100 * float(ex["met"].mean()),
         "sla_pct_ci_lo": 100 * bootstrap_ci(perq["met"], np.mean)[0],
         "sla_pct_ci_hi": 100 * bootstrap_ci(perq["met"], np.mean)[1],
         "sla_pct_seed_sd": 100 * float(ex.groupby("seed")["met"].mean().std(ddof=0)),
         "lat_mean_s": float(lat.mean()), "lat_p50_s": float(lat.quantile(.5)),
         "lat_p90_s": float(lat.quantile(.9)), "lat_p95_s": float(lat.quantile(.95)),
         "lat_p99_s": float(lat.quantile(.99)), "lat_max_s": float(lat.max()),
         "workload_time_s": per_seed("latency_s", "sum"),
         "slowdown_vs_static_geomean": float(np.exp(np.log(slow).mean())),
         "slowdown_vs_static_p90": float(slow.quantile(.9)), "slowdown_vs_static_p95": float(slow.quantile(.95)),
         "slowdown_vs_static_max": float(slow.max()),
         "slowdown_vs_oracle_geomean": float(np.exp(np.log(lat / ex["oracle"]).mean())),
         "sla_miss_overrun_p95": float((lat / ex["sla_target"])[~ex["met"]].quantile(.95)) if (~ex["met"]).any() else 0.0,
         "core_h": core_h, "search_core_h": search, "core_h_incl_search": core_h + search,
         "core_h_ci_lo": bootstrap_ci(perq["core_h"] / seeds, np.sum)[0],
         "core_h_ci_hi": bootstrap_ci(perq["core_h"] / seeds, np.sum)[1],
         "cpu_h_used": cpu_h, "cpu_util": cpu_h / core_h, "cpu_waste_h": core_h - cpu_h,
         "cpu_util_p50_per_run": float((ex["cpu_h"] / ex["core_h"]).median()),
         "mem_gb_h_alloc": per_seed("mem_gbh", "sum"),
         "mean_executors": float(ex["n"].mean()) if ex["n"].notna().any() else np.nan,
         "exact_label_pct": 100 * float((ex["n"] == ex["label"]).mean()) if ex["n"].notna().any() else np.nan,
         "over_provision_pct": 100 * float((ex["n"] > ex["label"]).mean()) if ex["n"].notna().any() else np.nan,
         "under_provision_pct": 100 * float((ex["n"] < ex["label"]).mean()) if ex["n"].notna().any() else np.nan,
         "decision_ms_p50": float(ex["decision_ms"].median()), "decision_ms_p99": float(ex["decision_ms"].quantile(.99))}
    # proposal C2: J = a*L + b*R + c*W + d*V with a=b=c=d=1 (the proposal gives no weights), each term
    # normalised per query by the static fixed_N run, V = 10 x relative SLA overrun (0 when met)
    c4, w4 = ex["query"].map(t[f"coreh_{n_max}"]), ex["query"].map(t[f"coreh_{n_max}"] - t[f"cpuh_{n_max}"])
    V = 10 * (lat / ex["sla_target"] - 1).clip(lower=0)
    m.update({"J_L": float((lat / ex["static"]).mean()), "J_R": float((ex["core_h"] / c4).mean()),
              "J_W": float(((ex["core_h"] - ex["cpu_h"]) / w4).mean()), "J_V": float(V.mean())})
    m["objective_J"] = m["J_L"] + m["J_R"] + m["J_W"] + m["J_V"]
    if "n_stage1" in ex and ex["n_stage1"].notna().any():
        under1 = ex["n_stage1"] < ex["label"]
        m["stage2_fired_pct"] = 100 * float((ex["n"] > ex["n_stage1"]).mean())
        m["stage1_under_pct"] = 100 * float(under1.mean())
        m["stage2_corrected_pct_of_under"] = 100 * float((ex["n"][under1] >= ex["label"][under1]).mean()) if under1.any() else np.nan
        m["fallback_pct"] = 100 * float(ex["fallback"].astype(bool).mean())
    return m


def paired_tests(ex_all: pd.DataFrame, baselines, policies):
    """Per-query median latency (all executions) paired across queries: Wilcoxon + Holm per baseline."""
    from scipy.stats import wilcoxon
    med = ex_all.groupby(["policy", "query"])["latency_s"].median().unstack("query")
    out = []
    for b in baselines:
        rows = []
        for p in policies:
            if p == b:
                continue
            d = (med.loc[p] - med.loc[b]).to_numpy()
            pv = 1.0 if np.allclose(d, 0) else float(wilcoxon(med.loc[p], med.loc[b]).pvalue)
            rows.append({"policy": p, "baseline": b, "geomean_lat_ratio": float(np.exp(np.log(med.loc[p] / med.loc[b]).mean())),
                         "wilcoxon_p": pv})
        # Holm-Bonferroni over every policy compared with this baseline
        order = np.argsort([r["wilcoxon_p"] for r in rows])
        m, running = len(rows), 0.0
        for rank, j in enumerate(order):
            running = max(running, min(1.0, (m - rank) * rows[j]["wilcoxon_p"]))
            rows[j]["wilcoxon_p_holm"] = running
        out += rows
    return pd.DataFrame(out)


def config_name(kind, mode, cal, s2, fb, safe=False, fallback=False):
    parts = (["S1"] + (["S2"] if s2 else []) + (["SAFE"] if safe else []) + (["FALLBACK"] if fallback else [])
             + (["CAL"] if cal else [])
             + ([f"FB-{fb}"] if fb != "none" else []))
    return f"prism{'-lm' if mode == 'lm' else ''}_{kind} [{'+'.join(parts)}]"


def prism_worker(task):
    """All component configurations of one (model kind, predictor mode); runs in its own process."""
    global JOBS, FEEDBACK_WEIGHT, RETRAIN_EVERY, DRIFT_Z, DRIFT_RATE
    (kind, mode, fbs, seeds_n, jobs, d) = task
    JOBS = jobs
    FEEDBACK_WEIGHT, RETRAIN_EVERY, DRIFT_Z, DRIFT_RATE = d["fb_consts"]
    out = []
    has_margin = any(d["margins"].get(f"{kind}|{mode}|stage{i}", 0.0) for i in (1, 2))
    for fb in fbs:
        for fbk in ((False, True) if fb == "none" and d["fallback"] else (False,)):   # fallback only without feedback (cost)
            for safe in ((False, True) if has_margin else (False,)):
                for s2 in (False, True):
                    for cal in (False, True):
                        seeds = range(seeds_n) if fb != "none" else range(1)
                        rows = [r for sd in seeds for r in run_prism(
                            d["test"], d["train"], d["tr2"], d["s1c"], d["s2c"], d["specs"], d["margins"], kind, mode,
                            cal, s2, fb, safe, sd, d["R"], d["n_max"], d["cap"], d["reps"], d["drift_baseline"],
                            fbk, d["ranges"], d["grow"])]
                        out.append((config_name(kind, mode, cal, s2, fb, safe, fbk),
                                    pd.DataFrame(rows).assign(search_core_h=0.0, kind=kind, mode=mode, cal=cal, s2=s2,
                                                              fb=fb, safe=safe, fallback_on=fbk)))
    return kind, mode, out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", type=Path, nargs="+",
                    default=[Path("results/measurements/training/initial")],
                    help="the training sweeps the --models were fit on")
    ap.add_argument("--test", type=Path, nargs="+", default=[Path("results/measurements/official_idle")],
                    help="test sweep dir(s) of the same queries (e.g. fixed-count sweep + a separate DRA run)")
    ap.add_argument("--models", type=Path, default=Path("prism/model/initial_training"),
                    help="manifest.json with the hyperparameters (and safety margins) tuned on the training queries")
    ap.add_argument("--kinds", default=",".join(MODEL_TYPES))
    ap.add_argument("--modes", default="label,lm")
    ap.add_argument("--fb", default=",".join(FB_MODES))
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--out", type=Path, default=Path("results/measurements/full_comparison"))
    ap.add_argument("--jobs", type=int, default=1, help="threads per model fit")
    ap.add_argument("--workers", type=int, default=10, help="processes, one (model, mode) each")
    ap.add_argument("--feedback-weight", type=float, default=FEEDBACK_WEIGHT)
    ap.add_argument("--retrain-every", type=int, default=RETRAIN_EVERY)
    ap.add_argument("--drift-z", type=float, default=DRIFT_Z)
    ap.add_argument("--drift-rate", type=float, default=DRIFT_RATE)
    ap.add_argument("--no-fallback", action="store_true", help="skip the FALLBACK configurations")
    ap.add_argument("--grow", type=Path, nargs="*", default=[],
                    help="measured growth-path runs (grow_<a>to<b>) of the same test queries, for Stage 2")
    args = ap.parse_args(argv)

    train, _, n_max, _ = table_of(args.train)
    test, dropped, _, truns = table_of(args.test)
    reps = rep_lookup(truns)
    R = int(truns.loc[truns["status"] == "SUCCESS", "rep"].max())
    test["sla_target"] = SLA_FACTOR * test[f"lat_{n_max}"]
    manifest = json.loads((args.models / "manifest.json").read_text())
    specs, margins = manifest["tuned_params"], manifest.get("safety_margins", {})
    s1c = [c for c in STAGE1_FEATURES if test[c].notna().all() and train[c].notna().all()]
    s2c = s1c + STAGE2_EXTRA
    tr2 = train[stage2_rows(train)]
    cap = calibration_cap(n_max)
    tb = train[train["true_post_shuffle_bytes"] > 0]
    drift_baseline = list((tb["true_post_shuffle_bytes"] - tb["estimated_shuffle_bytes"])
                          / tb["estimated_shuffle_bytes"].clip(lower=1.0))
    has_dra = any(k[1] == "dra" for k in reps)
    dra_missing = [q for q in test["query"] for r in range(1, R + 1) if (q, "dra", r) not in reps]
    if has_dra and dra_missing:   # a policy must be scored on every test query; never on a subset
        print(f"WARNING: spark_dra not measured for {len(dra_missing)} (query, round) pairs "
              f"({sorted(set(dra_missing))[:5]}...): DRA baseline left out of this comparison", flush=True)
        has_dra = False
    print(f"feedback weight {args.feedback_weight}, retrain every {args.retrain_every}, drift z {args.drift_z}, "
          f"drift rate {args.drift_rate}")
    print(f"train {len(train)} queries, test {len(test)} (dropped {dropped or 'none'}), rounds {R}, seeds {args.seeds}, "
          f"calibration cap {cap}/{n_max}, stage-2 rows test {int(stage2_rows(test).sum())}, DRA measured: {has_dra}, "
          f"safety margins: {margins or 'none'}", flush=True)
    args.out.mkdir(parents=True, exist_ok=True)

    ex = []
    def add(name, df, family):
        ex.append(df.assign(policy=name, family=family))

    # ---- baselines ----
    for n in range(1, n_max + 1):
        add(f"fixed_{n}e", fixed_policy_rows(test, pd.Series(n, index=test.index), R, reps), "baseline")
    add("heuristic", fixed_policy_rows(test, (test["input_size_bytes"] / 1e9 * 2.5 + 1).round().clip(1, n_max), R, reps), "baseline")
    if has_dra:
        add("spark_dra", fixed_policy_rows(test, None, R, reps, key="dra"), "baseline")
    add("lyu2020_rule", fixed_policy_rows(test, lyu_rule(test, n_max), R, reps), "baseline")
    n_off = offline_tuned_static(train, n_max)
    add(f"offline_tuned_static_lyu (n={n_off})", fixed_policy_rows(test, pd.Series(n_off, index=test.index), R, reps), "baseline")
    add("rios2018_rule", fixed_policy_rows(test, rios_rule(test, n_max), R, reps), "baseline")
    ch, cost = ernest_choice(test, n_max)
    add("ernest", fixed_policy_rows(test, ch, R, reps, extra_core_h=cost), "baseline")
    ch, cost = cherrypick_choice(test, n_max)
    add("cherrypick", fixed_policy_rows(test, ch, R, reps, extra_core_h=cost), "baseline")
    for kind, ch in original_prism_choices(test, n_max).items():
        add(f"prism_{kind} [original artifacts]", fixed_policy_rows(test, ch, R, reps), "original")
    add("oracle", fixed_policy_rows(test, test["label"], R, reps), "oracle")

    # ---- complete PRISM, every component combination, one process per (model, mode) ----
    from concurrent.futures import ProcessPoolExecutor
    shared = {"test": test, "train": train, "tr2": tr2, "s1c": s1c, "s2c": s2c, "specs": specs, "margins": margins,
              "R": R, "n_max": n_max, "cap": cap, "reps": reps, "drift_baseline": drift_baseline,
              "ranges": [(float(train[c].min()), float(train[c].max())) for c in s1c],
              "fb_consts": (args.feedback_weight, args.retrain_every, args.drift_z, args.drift_rate),
              "fallback": not args.no_fallback, "grow": grow_lookup(args.grow)}
    kinds = [k for k in args.kinds.split(",") if f"{k}|label|stage1" in specs]   # v1 models have no MLP
    print(f"models: {kinds}", flush=True)
    tasks = [(k, m, args.fb.split(","), args.seeds, args.jobs, shared) for k in kinds for m in args.modes.split(",")]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for kind, mode, out in pool.map(prism_worker, tasks):
            for name, df in out:
                add(name, df, "prism")
            print(f"  {kind:13s} {mode:5s} done ({time.time() - t0:.0f}s)", flush=True)

    ex = pd.concat(ex, ignore_index=True)
    ex.to_csv(args.out / "executions.csv", index=False)

    rows = []
    for (p, fam), g in ex.groupby(["policy", "family"], sort=False):
        meta = {c: g[c].iat[0] for c in ("kind", "mode", "cal", "s2", "fb", "safe", "fallback_on") if c in g and pd.notna(g[c].iat[0])}
        rows.append({"policy": p, "family": fam, **meta, **metrics(g, test, n_max)})
    pm = pd.DataFrame(rows)
    bases = [b for b in ["fixed_4e", "fixed_3e", "spark_dra", "cherrypick", "ernest"] if b in set(pm["policy"])]
    tests = paired_tests(ex, bases, list(pm["policy"]))
    for b in bases:
        tb_ = tests[tests["baseline"] == b].set_index("policy")
        pm[f"lat_ratio_vs_{b}"] = pm["policy"].map(tb_["geomean_lat_ratio"])
        pm[f"p_vs_{b}"] = pm["policy"].map(tb_["wilcoxon_p"])
        pm[f"p_holm_vs_{b}"] = pm["policy"].map(tb_["wilcoxon_p_holm"])
    # proposal expected result: waste (allocated-but-idle core-hours) reduction vs static and DRA
    for b in ("fixed_4e", "spark_dra"):
        if b in set(pm["policy"]):
            wb = float(pm.loc[pm["policy"] == b, "cpu_waste_h"].iat[0])
            pm[f"waste_reduction_vs_{b}_pct"] = 100 * (1 - pm["cpu_waste_h"] / wb)
    pm.to_csv(args.out / "policy_metrics.csv", index=False)
    tests.to_csv(args.out / "paired_tests.csv", index=False)

    # ---- ablation: each component's effect with everything else held fixed ----
    pr = pm[pm["family"] == "prism"].copy()
    pr["safe"] = pr["safe"].fillna(False).astype(bool)
    pr["fallback_on"] = pr["fallback_on"].fillna(False).astype(bool)
    key = ["kind", "mode", "cal", "s2", "fb", "safe", "fallback_on"]
    idx = pr.set_index(key)
    abl = []
    for comp, alts in (("cal", [(False, True)]), ("s2", [(False, True)]), ("safe", [(False, True)]), ("fallback_on", [(False, True)]),
                       ("fb", [("none", "drift"), ("none", "retrain"), ("none", "both")])):
        for off, on in alts:
            for k_, g in pr[pr[comp] == off].groupby(key):
                k_on = tuple(on if c == comp else v for c, v in zip(key, k_))
                if k_on not in idx.index:
                    continue
                a, b = idx.loc[k_], idx.loc[k_on]
                abl.append({"component": f"{comp}:{off}->{on}", **dict(zip(key, k_)),
                            "d_sla_pct": b["sla_pct"] - a["sla_pct"], "d_core_h": b["core_h"] - a["core_h"],
                            "d_lat_p95_s": b["lat_p95_s"] - a["lat_p95_s"],
                            "d_slowdown_geomean": b["slowdown_vs_static_geomean"] - a["slowdown_vs_static_geomean"],
                            "d_objective_J": b["objective_J"] - a["objective_J"], "d_cpu_waste_h": b["cpu_waste_h"] - a["cpu_waste_h"]})
    abl = pd.DataFrame(abl)
    abl.to_csv(args.out / "ablation.csv", index=False)
    abl_sum = abl.groupby("component")[["d_sla_pct", "d_core_h", "d_lat_p95_s", "d_objective_J"]].agg(
        ["mean", "min", "max"]).round(3) if len(abl) else pd.DataFrame()

    # feedback learning curve: SLA share per quarter of the delivered-query stream
    lc = ex[ex["family"] == "prism"].assign(met=lambda d: d["latency_s"] <= d["query"].map(test.set_index("query")["sla_target"]))
    lc["stream_quarter"] = (4 * lc["position"] // (len(test) * R)).astype(int) + 1
    lc = lc.groupby(["policy", "stream_quarter"]).agg(sla_pct=("met", lambda x: 100 * x.mean()), core_h=("core_h", "sum")).reset_index()
    lc["core_h"] /= lc["policy"].map(ex.groupby("policy")["seed"].nunique())
    lc.to_csv(args.out / "learning_curve.csv", index=False)

    cols = ["policy", "sla_pct", "sla_pct_ci_lo", "sla_pct_ci_hi", "lat_p50_s", "lat_p90_s", "lat_p95_s", "lat_p99_s",
            "slowdown_vs_static_geomean", "slowdown_vs_static_p95", "core_h_incl_search", "cpu_util", "mem_gb_h_alloc",
            "mean_executors", "under_provision_pct", "objective_J", "waste_reduction_vs_fixed_4e_pct", "p_vs_fixed_4e", "p_holm_vs_fixed_4e", "p_vs_fixed_3e", "p_holm_vs_fixed_3e"]
    top = pd.concat([pm[pm["family"] != "prism"], pr.sort_values(["sla_pct", "core_h"], ascending=[False, True]).head(15)])
    md = ["# Complete PRISM vs baselines (replay on measured 10 GB runs)\n",
          f"{len(test)} test queries ({args.test[0].parent.name}) x {R} rounds (round r = measured repetition r), {args.seeds} stream orders "
          f"for order-dependent (feedback) policies. SLA = {SLA_FACTOR} x median fixed_{n_max}e latency per query. "
          f"CAL = PRISM's original calibrate(): cap on an idle {n_max}-executor pool = {cap}. The v2 calibration used in the "
          f"v2 live runs applies no cap on an idle pool, so on these idle-cluster replays it equals the rows without CAL. "
          f"SAFE = safety margin tuned on training queries only. Memory = allocated GB-hours (peak use not measured).\n",
          "\n## Baselines and best 15 PRISM configurations\n", top[cols].to_markdown(index=False, floatfmt=".3g"),
          "\n\n## Component ablation (effect of switching a component on, all else equal; mean/min/max over models x modes x other components)\n",
          abl_sum.to_markdown() if len(abl_sum) else "_none_",
          "\n\nAll configurations: policy_metrics.csv; per-execution data: executions.csv; feedback learning curves: learning_curve.csv\n"]
    (args.out / "report.md").write_text("\n".join(md))
    print("\n".join(md))
    print(f"written to {args.out}")


if __name__ == "__main__":
    sys.exit(main())
