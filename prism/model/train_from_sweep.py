"""
Retrain PRISM allocation models from measured 10 GB executor sweeps and evaluate every policy.

Inputs: sweep directories from honest_benchmark.py (runs.csv + decisions.csv, each query measured at
1..N executors). Training sweeps = generated TPC-H-schema queries; --test = the 22 official queries.

Label (the PRISM objective, explicit): smallest executor count whose median latency is within
SLA_FACTOR of the fastest count; counts that time out are censored at the timeout.

Policies learned, for each of random forest / XGBoost / LightGBM / Ridge / SVR, Stage 1 (plan
features) and Stage 2 (+ shuffle bytes / partitions at the first AQE checkpoint):
  label : regress the label directly (original PRISM design)
  lm    : PRISM-LM, learn log-latency(features, n) from every measured count, pick the smallest n
          predicted within SLA_FACTOR of the predicted best
  +calibration variants apply PRISM's calibrate() cap (int(0.9 x available executors)).
Hyperparameters: grouped 5-fold CV on the training queries only, scored on the real objective
(share within SLA of the fastest count, minus a core-hour penalty).
Safety margin (v2, against under-provisioning): after the model hyperparameters, a margin is tuned the
same way (label: +0 / 0.25 / 0.5 executors before rounding; lm: SLA tolerance x exp(-0 / 0.05 / 0.10)).
Rows "...+safety" use it; the saved bundles include it (a tuned margin of 0 changes nothing).

Evaluation, always with the latencies actually measured at the chosen count:
  heldout_evaluation.csv : tuned + fit on training queries, scored on the test queries
  cv_all_evaluation.csv  : grouped K-fold over all queries (hyperparameters from the tuning step)
Baselines scored the same way: every fixed count, heuristic, real Spark DRA, Lyu/RIOS rules (repo
definitions), Ernest (full-scale profiling), CherryPick (GP/EI search with trial cost), the ORIGINAL
prism/model/baseline_models models, and the oracle.

Saved models (fit on training queries only) use the bundle format honest_benchmark.py loads:
  stage{1,2}_<model>.joblib and stage{1,2}_<model>_lm.joblib
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd

SLA_FACTOR = 1.15
STAGE1_FEATURES = ["input_size_bytes", "join_order_depth", "estimated_shuffle_bytes",
                   "stage_dag_depth", "stage_dag_branch_factor"]
STAGE2_EXTRA = ["true_post_shuffle_bytes", "true_partition_count"]
MODEL_TYPES = ["random_forest", "xgboost", "lightgbm", "ridge", "svr", "mlp"]
FILE_STEM = {"random_forest": "model", "xgboost": "xgboost", "lightgbm": "lightgbm",
             "ridge": "ridge", "svr": "svr", "mlp": "mlp"}


def build_model(kind: str, params: dict = None):
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler, FunctionTransformer
    log = FunctionTransformer(np.log1p)   # byte counts span 4+ orders of magnitude
    if kind == "random_forest":
        from sklearn.ensemble import RandomForestRegressor
        reg = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=0, n_jobs=-1)
    elif kind == "xgboost":
        from xgboost import XGBRegressor
        reg = XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=0, verbosity=0)
    elif kind == "lightgbm":
        from lightgbm import LGBMRegressor
        reg = LGBMRegressor(n_estimators=200, num_leaves=7, min_child_samples=3, learning_rate=0.05,
                            random_state=0, verbose=-1)
    elif kind == "ridge":
        from sklearn.linear_model import Ridge
        reg = Ridge(alpha=1.0)
    elif kind == "svr":
        from sklearn.svm import SVR
        reg = SVR(C=3.0, epsilon=0.2)
    elif kind == "mlp":   # the proposal's "lightweight neural regressor"
        from sklearn.neural_network import MLPRegressor
        reg = MLPRegressor(hidden_layer_sizes=(32, 16), alpha=1e-3, max_iter=3000, random_state=0)
    else:
        raise ValueError(kind)
    if params:
        reg.set_params(**params)
    return Pipeline([("log", log), ("scale", StandardScaler()), ("reg", reg)])


def load_sweeps(dirs):
    runs, decs, plans = [], [], []
    for d in dirs:
        r = pd.read_csv(d / "runs.csv")
        dc = pd.read_csv(d / "decisions.csv")
        ds = r["dataset"].iat[0] if "dataset" in r else d.name
        dc["dataset"] = ds
        runs.append(r)
        decs.append(dc)
        pf = d / "plan_features.csv"
        if pf.exists():
            p = pd.read_csv(pf)
            p["dataset"] = ds
            plans.append(p)
    return (pd.concat(runs, ignore_index=True), pd.concat(decs, ignore_index=True),
            pd.concat(plans, ignore_index=True) if plans else None)


def build_table(runs: pd.DataFrame, decs: pd.DataFrame, n_max: int, timeout_s: float = 1200.0,
                plan_feats: pd.DataFrame = None):
    # A count whose runs all TIMEOUT is kept as censored: latency = timeout (a lower bound),
    # so it can never be the label; any other failure drops the query.
    to = runs[(runs["status"] == "TIMEOUT") & runs["strategy"].str.match(r"^fixed_\d+e$")].copy()
    if len(to):
        to["latency_s"] = to["wall_s"].fillna(timeout_s)
        to["status"] = "SUCCESS"
        to["censored"] = True
        to["checksum"] = np.nan
        for c in ["executor_cpu_s", "alloc_core_s", "alloc_mem_gb_s"]:
            if c in to:
                to[c] = to[c].fillna(0)
        runs = pd.concat([runs[runs["status"] != "TIMEOUT"], to], ignore_index=True)
    for c in ["checkpoint_shuffle_bytes", "checkpoint_partitions", "executor_cpu_s", "alloc_mem_gb_s"]:
        if c not in runs:
            runs[c] = np.nan
    ok = runs[runs["status"] == "SUCCESS"]
    fixed = ok[ok["strategy"].str.match(r"^fixed_\d+e$")].copy()
    fixed["n"] = fixed["strategy"].str.extract(r"fixed_(\d+)e")[0].astype(int)
    med = fixed.groupby(["dataset", "query", "n"]).agg(
        latency=("latency_s", "median"), core_h=("alloc_core_s", lambda x: x.median() / 3600),
        cpu_h=("executor_cpu_s", lambda x: x.median() / 3600),
        mem_gbh=("alloc_mem_gb_s", lambda x: x.median() / 3600),
        first_latency=("latency_s", "first"),
        checksum=("checksum", lambda s: s.mode().iat[0] if s.notna().any() else np.nan),
        ckpt_bytes=("checkpoint_shuffle_bytes", "median"),
        ckpt_parts=("checkpoint_partitions", "median")).reset_index()
    dra = ok[ok["strategy"] == "spark_dra"].groupby(["dataset", "query"]).agg(
        dra_latency=("latency_s", "median"),
        dra_core_h=("alloc_core_s", lambda x: x.median() / 3600),
        dra_cpu_h=("executor_cpu_s", lambda x: x.median() / 3600),
        dra_mem_gbh=("alloc_mem_gb_s", lambda x: x.median() / 3600)).reset_index()

    feats = decs[decs["strategy"] == "fixed_1e"].drop_duplicates(["dataset", "query"])
    if plan_feats is not None:  # features recomputed with --plan-only override older decisions
        feats = feats.drop(columns=[c for c in STAGE1_FEATURES if c in feats]).merge(
            plan_feats[["dataset", "query"] + STAGE1_FEATURES], on=["dataset", "query"], how="left")
    rows, dropped = [], []
    for (ds, q), g in med.groupby(["dataset", "query"]):
        if set(g["n"]) != set(range(1, n_max + 1)) or g["checksum"].nunique() != 1:  # nunique skips NaN
            dropped.append(f"{ds}/{q}")
            continue
        g = g.set_index("n").sort_index()
        best = g["latency"].min()
        label = int(min(n for n in g.index if g.at[n, "latency"] <= SLA_FACTOR * best))
        row = {"dataset": ds, "query": q, "label": label, "fastest_n": int(g["latency"].idxmin()),
               "true_post_shuffle_bytes": float(g["ckpt_bytes"].median()),
               "true_partition_count": float(g["ckpt_parts"].median())}
        for n in g.index:
            row[f"lat_{n}"] = g.at[n, "latency"]
            row[f"coreh_{n}"] = g.at[n, "core_h"]
            row[f"cpuh_{n}"] = g.at[n, "cpu_h"]
            row[f"memgbh_{n}"] = g.at[n, "mem_gbh"]
            row[f"trial_{n}"] = g.at[n, "first_latency"]
        rows.append(row)
    if not rows:
        raise SystemExit(f"no query has successful runs at every count 1..{n_max} yet; dropped: {dropped}")
    tab = pd.DataFrame(rows).merge(feats[["dataset", "query"] + [c for c in STAGE1_FEATURES if c in feats]],
                                   on=["dataset", "query"], how="left").merge(dra, on=["dataset", "query"], how="left")
    return tab, dropped


def _pick(tab, choice, prefix):
    return pd.Series([tab.at[i, f"{prefix}_{int(c)}"] for i, c in choice.items()], index=tab.index)


def score(tab: pd.DataFrame, choice: pd.Series, n_max: int, name: str, dra=False, search_core_h=0.0) -> dict:
    if dra:
        lat, coreh, cpuh, memh = tab["dra_latency"], tab["dra_core_h"], tab["dra_cpu_h"], tab["dra_mem_gbh"]
    else:
        lat, coreh, cpuh, memh = (_pick(tab, choice, p) for p in ("lat", "coreh", "cpuh", "memgbh"))
    static = tab[f"lat_{n_max}"]
    out = {"policy": name, "queries": int(lat.notna().sum()),
           "sla_pct_vs_static": 100 * float((lat <= SLA_FACTOR * static).mean()),
           "within_1.15x_oracle_pct": 100 * float((lat <= SLA_FACTOR * tab[[f"lat_{n}" for n in range(1, n_max + 1)]].min(axis=1)).mean()),
           "geomean_lat_vs_static": float(np.exp(np.mean(np.log(lat / static)))),
           "geomean_lat_vs_fixed3": float(np.exp(np.mean(np.log(lat / tab["lat_3"])))) if "lat_3" in tab else np.nan,
           "total_core_h": float(coreh.sum()),
           "total_cpu_waste_h": float((coreh - cpuh).sum()),
           "median_cpu_util": float((cpuh / coreh).median()),
           "total_mem_gb_h": float(memh.sum()),
           "search_core_h": float(search_core_h),
           "label_accuracy_pct": 100 * float((choice == tab["label"]).mean()) if not dra else np.nan,
           "distinct_choices": int(choice.nunique()) if not dra else np.nan}
    try:
        from scipy.stats import wilcoxon
        for b, col in [("static", f"lat_{n_max}"), ("fixed3", "lat_3")]:
            d = lat - tab[col]
            out[f"wilcoxon_p_vs_{b}"] = 1.0 if np.allclose(d, 0) else float(wilcoxon(lat, tab[col]).pvalue)
    except Exception:
        pass
    return out


def offline_tuned_static(train, n_max):
    """Lyu et al. (PVLDB'20)-style offline-tuned static configuration: the one executor count with the best
    tuning objective on the TRAINING queries, then applied unchanged to every test query."""
    return max(range(1, n_max + 1), key=lambda n: objective(train, pd.Series(n, index=train.index), n_max))


def baseline_results(ev, n_max, train=None):
    """Every non-learned policy, scored on the evaluation rows `ev`."""
    res = [score(ev, pd.Series(n, index=ev.index), n_max, f"fixed_{n}e") for n in range(1, n_max + 1)]
    if train is not None:
        n_off = offline_tuned_static(train, n_max)
        res.append(score(ev, pd.Series(n_off, index=ev.index), n_max, f"offline_tuned_static (Lyu-style, n={n_off})"))
    heur = (ev["input_size_bytes"] / 1e9 * 2.5 + 1).round().clip(1, n_max).astype(int)
    res.append(score(ev, heur, n_max, "heuristic"))
    if ev["dra_latency"].notna().all():
        res.append(score(ev, pd.Series(n_max, index=ev.index), n_max, "spark_dra", dra=True))
    res.append(score(ev, ev["label"], n_max, "oracle (label)"))
    res.append(score(ev, lyu_rule(ev, n_max), n_max, "lyu2020_rule (repo definition)"))
    res.append(score(ev, rios_rule(ev, n_max), n_max, "rios2018_rule (repo definition)"))
    ern, ern_cost = ernest_choice(ev, n_max)
    res.append(score(ev, ern, n_max, "ernest (full-scale profiling at n=1,N; probes counted)",
                     search_core_h=ern_cost))
    cp, cp_cost = cherrypick_choice(ev, n_max)
    res.append(score(ev, cp, n_max, "cherrypick (GP/EI search, trials counted)", search_core_h=cp_cost))
    for kind, ch in original_prism_choices(ev, n_max).items():
        res.append(score(ev, ch, n_max, f"prism_{kind}_original_artifacts"))
    return res


def stage2_rows(t):
    return t[STAGE2_EXTRA].notna().all(axis=1) & (t["true_post_shuffle_bytes"] > 0)


# ---- policies: "label" = regress the best executor count directly (original PRISM design);
#      "lm" = PRISM-LM: learn log-latency as a function of (plan features, n) from every measured
#      count, then pick the smallest n predicted within SLA_FACTOR of the predicted best ----
GRIDS = {
    "random_forest": [{"min_samples_leaf": l, "max_depth": d} for l in (1, 2, 4) for d in (None, 8)],
    "xgboost": [{"max_depth": d, "n_estimators": n, "learning_rate": lr}
                for d in (2, 3, 5) for n in (150, 400) for lr in (0.05, 0.1)],
    "lightgbm": [{"num_leaves": l, "n_estimators": n, "min_child_samples": c}
                 for l in (7, 15) for n in (150, 400) for c in (3, 10)],
    "ridge": [{"alpha": a} for a in (0.1, 1.0, 10.0)],
    "svr": [{"C": c, "epsilon": e} for c in (1.0, 3.0, 10.0) for e in (0.1, 0.3)],
    "mlp": [{"hidden_layer_sizes": h, "alpha": a} for h in ((16,), (32, 16), (64, 32)) for a in (1e-4, 1e-2)],
}


def _long(t, cols, n_max):
    """One row per (query, n) with log latency as target."""
    X, y = [], []
    for _, r in t.iterrows():
        for n in range(1, n_max + 1):
            X.append([r[c] for c in cols] + [float(n)])
            y.append(np.log(r[f"lat_{n}"]))
    return np.array(X, float), np.array(y, float)


class _LatencyPolicy:
    """PRISM-LM as a bundle the harness can call: predict(X) -> chosen executor count per row."""

    def __init__(self, model, cols, n_max, sla=SLA_FACTOR):
        self.model, self.cols, self.n_max, self.sla = model, cols, n_max, sla

    def choose(self, F: np.ndarray) -> np.ndarray:
        F = np.asarray(F, float)
        ns = np.arange(1, self.n_max + 1, dtype=float)
        grid = np.column_stack([np.repeat(F, len(ns), axis=0), np.tile(ns, len(F))])
        pred = self.model.predict(grid).reshape(len(F), len(ns))         # one call for all rows
        ok = pred <= pred.min(axis=1, keepdims=True) + np.log(self.sla)
        return (ok.argmax(axis=1) + 1).astype(float)                      # smallest n within SLA

    def predict(self, X):
        F = X[self.cols].to_numpy(float) if hasattr(X, "columns") else np.asarray(X, float)
        return self.choose(F)


MARGINS = {"label": [0.0, 0.25, 0.5], "lm": [0.0, 0.05, 0.10]}


def fit_policy(train, cols, kind, mode, params, n_max, margin=0.0):
    if mode == "label":
        m = build_model(kind, params).fit(train[cols].to_numpy(float), train["label"].to_numpy(float))
        return lambda t: pd.Series(np.clip(np.round(m.predict(t[cols].to_numpy(float)) + margin), 1, n_max).astype(int),
                                   index=t.index), m
    X, y = _long(train, cols, n_max)
    pol = _LatencyPolicy(build_model(kind, params).fit(X, y), cols, n_max, sla=SLA_FACTOR * np.exp(-margin))
    return lambda t: pd.Series(pol.choose(t[cols].to_numpy(float)).astype(int), index=t.index), pol


def objective(t, choice, n_max):
    """Tuning score on the real goal: share within SLA_FACTOR of the fastest count, then core-hours."""
    lat = _pick(t, choice, "lat")
    best = t[[f"lat_{n}" for n in range(1, n_max + 1)]].min(axis=1)
    coreh = _pick(t, choice, "coreh")
    oracle_coreh = _pick(t, t["label"], "coreh")
    return float((lat <= SLA_FACTOR * best).mean()) - 0.25 * float((coreh / oracle_coreh).mean() - 1.0)


def tune(train, cols, kind, mode, n_max, folds=5):
    """Model hyperparameters (margin 0), then the safety margin with those hyperparameters."""
    from sklearn.model_selection import GroupKFold
    k = min(folds, train["query"].nunique())
    splits = list(GroupKFold(n_splits=k).split(train, groups=train["query"]))

    def cv(params, margin):
        scores = []
        for tr, va in splits:
            chooser, _ = fit_policy(train.iloc[tr], cols, kind, mode, params, n_max, margin)
            scores.append(objective(train.iloc[va], chooser(train.iloc[va]), n_max))
        return float(np.mean(scores))

    rows = [{"model": kind, "mode": mode, "params": json.dumps(p), "margin": 0.0, "cv_objective": cv(p, 0.0)}
            for p in GRIDS[kind]]
    best = json.loads(max(rows, key=lambda r: r["cv_objective"])["params"])
    mrows = [{"model": kind, "mode": mode, "params": json.dumps(best), "margin": m, "cv_objective": cv(best, m)}
             for m in MARGINS[mode][1:]]
    rows += mrows
    cand = [r for r in rows if r["params"] == json.dumps(best)]   # margin 0 first: ties keep no margin
    margin = max(cand, key=lambda r: r["cv_objective"])["margin"]
    return best, rows, margin


def model_results(ev, choices, n_max, tag):
    """choices: {(kind, mode, stage): Series over the ev rows that have a prediction}"""
    res, cap = [], max(1, int(n_max * 0.9))  # PRISM calibrate(): int(0.9 x available) = 3 of 4 when idle
    for (kind, mode, stage), ch in choices.items():
        sub = ev.loc[ch.index]
        name = f"prism{'-lm' if mode == 'lm' else ''}_{kind}_{stage}"
        res.append(score(sub, ch, n_max, f"{name} ({tag})"))
        res.append(score(sub, ch.clip(upper=cap), n_max, f"{name}+calibration ({tag})"))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sweeps", nargs="+", type=Path, help="training sweeps")
    ap.add_argument("--test", nargs="*", type=Path, default=[],
                    help="held-out sweeps: models are tuned and fit on the training sweeps only and scored here")
    ap.add_argument("--cv-folds", type=int, default=10, help="grouped folds for the all-queries evaluation")
    ap.add_argument("--out", type=Path, default=Path("prism/model/initial_training"))
    args = ap.parse_args(argv)

    def table_of(dirs):
        runs, decs, pf = load_sweeps(dirs)
        n = int(runs["strategy"].str.extract(r"fixed_(\d+)e")[0].dropna().astype(int).max())
        t, dr = build_table(runs, decs, n, plan_feats=pf)
        return t, dr, n

    train, dropped, n_max = table_of(args.sweeps)
    test, dropped_t, _ = table_of(args.test) if args.test else (None, [], n_max)
    allq = pd.concat([train, test], ignore_index=True) if test is not None else train
    s1 = [c for c in STAGE1_FEATURES if c in allq and allq[c].notna().all()]
    s2 = s1 + STAGE2_EXTRA
    print(f"train: {len(train)} queries; dropped {len(dropped)}: {dropped or 'none'}")
    if test is not None:
        print(f"test:  {len(test)} queries; dropped {len(dropped_t)}: {dropped_t or 'none'}")
    print(f"stage1 features: {s1}")
    print("train labels:", train["label"].value_counts().sort_index().to_dict(),
          "| test labels:", test["label"].value_counts().sort_index().to_dict() if test is not None else "-")
    args.out.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 260)
    fmt = lambda x: f"{x:.3f}"

    # 1) hyperparameter tuning: grouped CV on the TRAINING queries only
    tr2 = train[stage2_rows(train)]
    specs, tuning_rows = {}, []
    for kind in MODEL_TYPES:
        for mode in ("label", "lm"):
            for stage, cols, data in (("stage1", s1, train), ("stage2", s2, tr2)):
                if len(data) < 10:
                    continue
                params, rows, margin = tune(data, cols, kind, mode, n_max)
                specs[(kind, mode, stage)] = (cols, params, margin)
                tuning_rows += [{**r, "stage": stage} for r in rows]
                print(f"[tune] {kind:13s} {mode:5s} {stage}: {params} margin={margin}")
    pd.DataFrame(tuning_rows).to_csv(args.out / "tuning.csv", index=False)

    # 2) held-out: fit on training queries, score on the test queries
    fitted, fitted_safe = {}, {}
    for key, (cols, params, margin) in specs.items():
        kind, mode, stage = key
        data = tr2 if stage == "stage2" else train
        fitted[key] = fit_policy(data, cols, kind, mode, params, n_max)
        fitted_safe[key] = fit_policy(data, cols, kind, mode, params, n_max, margin)
    if test is not None:
        choices = {}
        te2 = test[stage2_rows(test)]
        for key in fitted:
            ev = te2 if key[2] == "stage2" else test
            if len(ev):
                choices[key] = fitted[key][0](ev)
                choices[(key[0], key[1], key[2] + "+safety")] = fitted_safe[key][0](ev)
        held = pd.DataFrame(baseline_results(test, n_max, train) + model_results(test, choices, n_max, "held-out"))
        print("\n=== HELD-OUT: tuned + trained on training queries, scored on test queries ===")
        print(held.to_string(index=False, float_format=fmt))
        held.to_csv(args.out / "heldout_evaluation.csv", index=False)
        pd.DataFrame({"query": test["query"], "label": test["label"],
                      **{f"{k}_{m}_{s}": v for (k, m, s), v in choices.items()}}).to_csv(
            args.out / "heldout_choices.csv", index=False)

    # 3) grouped K-fold over ALL queries (hyperparameters fixed from step 1)
    from sklearn.model_selection import GroupKFold
    choices = {}
    has2 = stage2_rows(allq)
    for key, (cols, params, margin) in specs.items():
        kind, mode, stage = key
        sub = allq[has2] if stage == "stage2" else allq
        k = min(args.cv_folds, sub["query"].nunique())
        for suffix, mg in [("", 0.0)] + ([("+safety", margin)] if margin else []):
            ch = pd.Series(0, index=sub.index)
            for tr, te in GroupKFold(n_splits=k).split(sub, groups=sub["query"]):
                chooser, _ = fit_policy(sub.iloc[tr], cols, kind, mode, params, n_max, mg)
                ch.iloc[te] = chooser(sub.iloc[te]).to_numpy()
            choices[(kind, mode, stage + suffix)] = ch
    cv = pd.DataFrame(baseline_results(allq, n_max) + model_results(allq, choices, n_max, f"{args.cv_folds}-fold grouped CV"))
    print(f"\n=== {args.cv_folds}-FOLD GROUPED CV over all {len(allq)} queries ===")
    print(cv.to_string(index=False, float_format=fmt))
    cv.to_csv(args.out / "cv_all_evaluation.csv", index=False)
    allq.to_csv(args.out / "training_table.csv", index=False)

    # 4) final models for live runs: tuned + fit on the TRAINING queries only
    from prism.model.train_from_sweep import _Named as Named, _LatencyPolicy as LP  # importable, not __main__
    for (kind, mode, stage), (_, model) in fitted_safe.items():
        cols, _, margin = specs[(kind, mode, stage)]
        if mode == "lm":
            model = LP(model.model, cols, n_max, sla=SLA_FACTOR * np.exp(-margin))
            stem = f"{FILE_STEM[kind]}_lm"
        else:
            model = Named(model, cols, margin)
            stem = FILE_STEM[kind]
        joblib.dump({"model": model, "feature_columns": cols, "model_type": kind, "mode": mode,
                     "params": specs[(kind, mode, stage)][1], "safety_margin": margin, "target": "num_executors",
                     "label_rule": f"min n with latency <= {SLA_FACTOR} x best"},
                    args.out / f"{stage}_{stem}.joblib")
    (args.out / "manifest.json").write_text(json.dumps({
        "train_sweeps": [str(p) for p in args.sweeps], "test_sweeps": [str(p) for p in args.test],
        "train_queries": len(train), "test_queries": 0 if test is None else len(test),
        "dropped": dropped + dropped_t, "stage1_features": s1, "stage2_features": s2, "n_max": n_max,
        "sla_factor": SLA_FACTOR, "tuned_params": {f"{k}|{m}|{s}": v[1] for (k, m, s), v in specs.items()},
        "safety_margins": {f"{k}|{m}|{s}": v[2] for (k, m, s), v in specs.items()},
        "saved_models_fit_on": "training sweeps only",
        "evaluation": "held-out (train->test) + grouped K-fold over all, scored with measured sweep latencies"},
        indent=2))
    print(f"\nwritten to {args.out}")


def lyu_rule(tab, n_max):
    """soa_baselines.evaluate_lyu_2020 executor rule, clamped to the pool."""
    total = tab["input_size_bytes"] + tab["estimated_shuffle_bytes"]
    return np.ceil(total / (256.0 * 1024 * 1024)).clip(2, 8).clip(1, n_max).astype(int)


def rios_rule(tab, n_max):
    """soa_baselines.evaluate_rios_2018 executor rule (no co-located jobs), clamped to the pool."""
    base = np.ceil(tab["input_size_bytes"] / (200.0 * 1024 * 1024)).clip(1, 8)
    return np.floor(base * 1.0).clip(1, n_max).astype(int)


def ernest_choice(tab, n_max, probes=(1, None)):
    """Ernest (NSDI'16) adapted to a single (10 GB) scale: fit t(n) = th0 + th1/n + th2*log n + th3*n
    (th >= 0, NNLS) on profiling runs of the SAME query at n=1 and n=N (their first measured
    repetition), then pick the smallest n predicted within SLA_FACTOR of the predicted best.
    Ernest's original method profiles on data subsets; here profiling is on the full data, and its
    cost is returned as search core-hours."""
    from scipy.optimize import nnls
    probes = [p or n_max for p in probes]
    choice, cost_h = pd.Series(0, index=tab.index), 0.0
    feats = lambda n: [1.0, 1.0 / n, np.log(n), float(n)]
    for i in tab.index:
        X = np.array([feats(n) for n in probes])
        y = np.array([tab.at[i, f"trial_{n}"] for n in probes])
        cost_h += sum(tab.at[i, f"coreh_{n}"] for n in probes)
        th, _ = nnls(X, y)
        pred = {n: float(th @ feats(n)) for n in range(1, n_max + 1)}
        best = min(pred.values())
        choice[i] = min(n for n in pred if pred[n] <= SLA_FACTOR * best)
    return choice, cost_h


def cherrypick_choice(tab, n_max, ei_stop=0.10):
    """CherryPick (EuroSys'17) over n in 1..N: GP on observed cost (core-seconds) with the SLA
    (1.15 x static) as a constraint, expected-improvement acquisition, stop when EI < 10% of best.
    Each trial is a real measured run (first repetition); its core-hours are counted as search cost."""
    from scipy.stats import norm
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern, WhiteKernel
    choice, cost_h = pd.Series(0, index=tab.index), 0.0
    for i in tab.index:
        sla = SLA_FACTOR * tab.at[i, f"lat_{n_max}"]
        obs = {}
        def trial(n):
            nonlocal cost_h
            lat = tab.at[i, f"trial_{n}"]
            cost_h += tab.at[i, f"coreh_{n}"]
            obs[n] = (lat, n * lat if lat <= sla else 10 * n_max * sla)
        trial(1); trial(n_max)
        while len(obs) < n_max:
            xs = np.array(sorted(obs))[:, None].astype(float)
            ys = np.array([obs[n][1] for n in sorted(obs)])
            gp = GaussianProcessRegressor(Matern(nu=2.5) + WhiteKernel(1e-3), normalize_y=True).fit(xs, ys)
            cand = np.array([n for n in range(1, n_max + 1) if n not in obs])[:, None].astype(float)
            mu, sd = gp.predict(cand, return_std=True)
            best = ys.min()
            z = (best - mu) / np.maximum(sd, 1e-9)
            ei = (best - mu) * norm.cdf(z) + sd * norm.pdf(z)
            if ei.max() < ei_stop * best:
                break
            trial(int(cand[int(np.argmax(ei))][0]))
        feasible = {n: v for n, v in obs.items() if v[0] <= sla}
        pool = feasible or obs
        choice[i] = min(pool, key=lambda n: pool[n][1])
    return choice, cost_h


def original_prism_choices(tab, n_max):
    """Executor counts the ORIGINAL prism/model/baseline_models models choose on these queries."""
    from prism.evaluation.honest_benchmark import load_bundles, predict, calibrated_count, Pool
    from prism.shared.schemas import FeatureVector, PlanFeatures, ClusterLoadFeatures, AqeCorrection
    bundles = load_bundles(PROJECT_ROOT / "prism" / "model" / "baseline_models")
    pool = Pool(n_max, 2, 1536)
    out = {k: pd.Series(0, index=tab.index) for k in bundles}
    for i, r in tab.iterrows():
        fv = FeatureVector(query_id=r["query"], stage="submission", plan_features=PlanFeatures(
            input_size_bytes=r["input_size_bytes"], join_type="sort_merge",
            join_order_depth=int(r["join_order_depth"]), estimated_shuffle_bytes=r["estimated_shuffle_bytes"],
            stage_dag_depth=int(r.get("stage_dag_depth", 3) if pd.notna(r.get("stage_dag_depth", np.nan)) else 3),
            stage_dag_branch_factor=int(r.get("stage_dag_branch_factor", 2) if pd.notna(r.get("stage_dag_branch_factor", np.nan)) else 2)),
            cluster_load_features=ClusterLoadFeatures(queue_depth=0, available_executors=n_max,
                                                      available_cores=2 * n_max, colocated_job_count=0),
            aqe_correction=AqeCorrection())
        for k, b in bundles.items():
            e, c, m = predict(b["stage1"], fv)
            out[k][i] = calibrated_count(e, c, m, pool)[0]
    return out


class _Named:
    """Accepts the DataFrame honest_benchmark passes and feeds the fitted pipeline in column order."""

    def __init__(self, model, cols, margin=0.0):
        self.model, self.cols, self.margin = model, cols, margin

    def predict(self, X):
        X = X[self.cols].to_numpy(float) if hasattr(X, "columns") else np.asarray(X, float)
        return self.model.predict(X) + getattr(self, "margin", 0.0)   # v1 bundles have no margin


if __name__ == "__main__":
    sys.exit(main())
