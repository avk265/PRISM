"""
Sensitivity of results to the weights of the proposal's objective J = a*L + b*R + c*W + d*V (C2).

Per query and executor count n (medians of the measured runs), every term normalised by the static fixed_N run:
  L = latency_n / latency_N        R = core_h_n / core_h_N
  W = waste_n / waste_N            (waste = allocated - used core-hours)
  V = 10 x max(0, latency_n / SLA - 1),  SLA = SLA_FACTOR x latency_N

Part A  post-hoc: J of every policy in a full_comparison run (executions.csv) over a weight grid -> which
        policy wins under which weights, and the rank of the best PRISM configuration. Choosing a winner on the
        test set is optimistic; this is a sensitivity view, not a model-selection result.
Part B  objective-driven PRISM: for each named weight setting, everything is chosen on the TRAINING queries only
        (grouped 5-fold CV) and then scored on each test set:
          prism[-lm]_<model>_<stage> +margin(J)  safety margin tuned for J on training CV
          prism-lm-J_<model>_<stage>             decides per query: n = argmin predicted J (the latency model
                                                 predicts L, R = n x L x N^-1 shape, V from predicted latency;
                                                 W is not predictable from the plan and is left to the margin)
          fixed_tuned_J                          best single executor count for J on the training queries
          oracle_J                               per-query argmin of measured J (upper bound)
        <stage> = stage2 starts the query at the Stage 1 choice of the same variant and grows it to
        max(Stage 1, Stage 2) at the first shuffle; a grown query is scored with the measured growth-path run
        (median of its repetitions, --grow), never with a run that had the final count from the start.
Outputs (--out): part_a_winners.csv, part_a_ranks.csv, part_b.csv, report.md
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from prism.model.train_from_sweep import (SLA_FACTOR, STAGE1_FEATURES, STAGE2_EXTRA, MODEL_TYPES, build_model,
                                          _long, stage2_rows)
from prism.evaluation.full_comparison import table_of

NAMED = {  # (a, b, c, d)
    "balanced": (1, 1, 1, 1), "latency_first": (2, 0.5, 0.5, 1), "cost_first": (0.5, 2, 1, 1),
    "waste_first": (0.5, 1, 2, 1), "sla_strict": (1, 1, 1, 5), "sla_relaxed": (1, 1, 1, 0.25),
    "cost_only_sla_strict": (0, 1, 0, 5), "latency_only": (1, 0, 0, 0),
}
# no margin first: on a tie in training CV, min() keeps the plain model
MARGINS = {"label": [0.0, -0.25, 0.25, -0.5, 0.5, 0.75, 1.0], "lm": [0.0, -0.05, 0.05, -0.10, 0.10, 0.15, 0.20]}


# Per-query audit trail for independent arithmetic and measured-path verification.
AUDIT_ROWS = []
def trace_summary(t, start, final, lat, core, cpu, weights, policy):
    for i in final.index:
        AUDIT_ROWS.append(dict(query=t.at[i, 'query'], policy=policy,
            weights=next(k for k,v in NAMED.items() if tuple(v)==tuple(weights)),
            start=int(start[i]), final=int(final[i]), latency_s=float(lat[i]),
            core_h=float(core[i]), cpu_h=float(cpu[i]),
            reference_latency_s=float(t.at[i,'lat_4']),
            reference_core_h=float(t.at[i,'coreh_4']),
            reference_cpu_h=float(t.at[i,'cpuh_4'])))


def terms(t: pd.DataFrame, n_max: int):
    """{n: DataFrame[L, R, W, V]} per query for every executor count (median measurements)."""
    out = {}
    sla = SLA_FACTOR * t[f"lat_{n_max}"]
    wN = (t[f"coreh_{n_max}"] - t[f"cpuh_{n_max}"]).clip(lower=1e-9)
    for n in range(1, n_max + 1):
        out[n] = pd.DataFrame({"L": t[f"lat_{n}"] / t[f"lat_{n_max}"], "R": t[f"coreh_{n}"] / t[f"coreh_{n_max}"],
                               "W": (t[f"coreh_{n}"] - t[f"cpuh_{n}"]) / wN,
                               "V": 10 * (t[f"lat_{n}"] / sla - 1).clip(lower=0)}, index=t.index)
    return out


def grow_medians(d: Path):
    """{(query, a, b): (latency_s, core_h, cpu_h)} medians of the measured growth-path runs grow_<a>to<b>."""
    r = pd.read_csv(Path(d) / "runs.csv")
    r = r[r["strategy"].str.match(r"^grow_\d+to\d+$") & r["status"].isin(["SUCCESS", "TIMEOUT"])].copy()
    r.loc[r["status"] == "TIMEOUT", "latency_s"] = r.loc[r["status"] == "TIMEOUT", "wall_s"]
    r["core_h"], r["cpu_h"] = r["alloc_core_s"].fillna(0) / 3600, r["executor_cpu_s"].fillna(0) / 3600
    g = r.groupby(["query", "strategy"])[["latency_s", "core_h", "cpu_h"]].median()
    out = {}
    for (q, st), v in g.iterrows():
        a, b = (int(x) for x in st[len("grow_"):].split("to"))
        out[(q, a, b)] = (float(v.latency_s), float(v.core_h), float(v.cpu_h))
    return out


def summary_path(t, start, final, w, n_max, name, gm):
    """summary() for Stage 2 choices: a query whose count grows start -> final uses its growth-path run."""
    lat, core, cpu = [], [], []
    for i in final.index:
        a, b = int(start[i]), int(final[i])
        if b > a:
            if (t.at[i, "query"], a, b) not in gm:
                raise KeyError(f"no measured growth run {t.at[i, 'query']} {a}->{b} (pass --grow)")
            x = gm[(t.at[i, "query"], a, b)]
        else:
            x = (t.at[i, f"lat_{b}"], t.at[i, f"coreh_{b}"], t.at[i, f"cpuh_{b}"])
        lat.append(x[0]); core.append(x[1]); cpu.append(x[2])
    lat, core, cpu = (pd.Series(v, index=final.index) for v in (lat, core, cpu))
    trace_summary(t, start, final, lat, core, cpu, w, name)
    latN, coreN = t.loc[final.index, f"lat_{n_max}"], t.loc[final.index, f"coreh_{n_max}"]
    wN = (coreN - t.loc[final.index, f"cpuh_{n_max}"]).clip(lower=1e-9)
    sla = SLA_FACTOR * latN
    T = np.column_stack([lat / latN, core / coreN, (core - cpu) / wN, 10 * (lat / sla - 1).clip(lower=0)])
    return {"policy": name, "J": float((T @ np.array(w, float)).mean()), "sla_pct": 100 * float((lat <= sla).mean()),
            "core_h": float(core.sum()), "mean_n": float(final.mean())}


def J_of(T, choice, w):
    a, b, c, d = w
    rows = np.array([T[int(n)].loc[i].to_numpy() for i, n in choice.items()])
    return float((rows @ np.array([a, b, c, d], float)).mean())


def summary(t, T, choice, w, n_max, name):
    lat = pd.Series([t.at[i, f"lat_{int(n)}"] for i, n in choice.items()], index=choice.index)
    core = pd.Series([t.at[i, f"coreh_{int(n)}"] for i, n in choice.items()], index=choice.index)
    cpu = pd.Series([t.at[i, f"cpuh_{int(n)}"] for i,n in choice.items()], index=choice.index)
    trace_summary(t, choice, choice, lat, core, cpu, w, name)
    return {"policy": name, "J": J_of(T, choice, w), "sla_pct": 100 * float((lat <= SLA_FACTOR * t[f"lat_{n_max}"]).mean()),
            "core_h": float(core.sum()), "mean_n": float(choice.mean())}


# ---------------------------- Part A ----------------------------
def part_a(fc_dir: Path, test: pd.DataFrame, n_max: int):
    ex = pd.read_csv(fc_dir / "executions.csv")
    t = test.set_index("query")
    st, sla = ex["query"].map(t[f"lat_{n_max}"]), SLA_FACTOR * ex["query"].map(t[f"lat_{n_max}"])
    c4 = ex["query"].map(t[f"coreh_{n_max}"])
    w4 = ex["query"].map(t[f"coreh_{n_max}"] - t[f"cpuh_{n_max}"]).clip(lower=1e-9)
    ex = ex.assign(L=ex["latency_s"] / st, R=ex["core_h"] / c4, W=(ex["core_h"] - ex["cpu_h"]) / w4,
                   V=10 * (ex["latency_s"] / sla - 1).clip(lower=0))
    per = ex.groupby(["policy", "family"])[["L", "R", "W", "V"]].mean().reset_index()
    grid = [w for w in itertools.product([0, 0.5, 1, 2], [0, 0.5, 1, 2], [0, 0.5, 1, 2], [0.25, 1, 5]) if any(w[:3])]
    wins, ranks = [], []
    for w in grid:
        j = per[["L", "R", "W", "V"]].to_numpy() @ np.array(w, float)
        p = per.assign(J=j).sort_values("J")
        best = p.iloc[0]
        nonoracle = p[p["family"] != "oracle"]
        bp = nonoracle[nonoracle["family"] == "prism"].iloc[0] if (nonoracle["family"] == "prism").any() else None
        bb = nonoracle[nonoracle["family"] == "baseline"].iloc[0]
        wins.append({"a": w[0], "b": w[1], "c": w[2], "d": w[3], "winner_excl_oracle": nonoracle.iloc[0]["policy"],
                     "winner_family": nonoracle.iloc[0]["family"], "best_prism": None if bp is None else bp["policy"],
                     "best_prism_J": None if bp is None else bp["J"], "best_baseline": bb["policy"], "best_baseline_J": bb["J"],
                     "prism_beats_all_baselines": bool(bp is not None and bp["J"] < bb["J"]), "oracle_J": float(p[p["family"] == "oracle"]["J"].min())})
        nonoracle = nonoracle.reset_index(drop=True)
        for fam in ("prism", "baseline", "original"):
            sub = nonoracle[nonoracle["family"] == fam]
            if len(sub):
                ranks.append({"a": w[0], "b": w[1], "c": w[2], "d": w[3], "family": fam,
                              "best_rank": int(sub.index.min()) + 1, "of": len(nonoracle)})
    return pd.DataFrame(wins), pd.DataFrame(ranks)


# ---------------------------- Part B ----------------------------
def fit_predict(kind, mode, params, tr, te, cols, n_max):
    """label: raw predicted count per te row; lm: predicted log-latency matrix (rows x n)."""
    if mode == "label":
        m = build_model(kind, params).fit(tr[cols].to_numpy(float), tr["label"].to_numpy(float))
        return m.predict(te[cols].to_numpy(float))
    X, y = _long(tr, cols, n_max)
    m = build_model(kind, params).fit(X, y)
    F = te[cols].to_numpy(float)
    ns = np.arange(1, n_max + 1, dtype=float)
    grid = np.column_stack([np.repeat(F, len(ns), axis=0), np.tile(ns, len(F))])
    return m.predict(grid).reshape(len(F), len(ns))


def choose(mode, pred, margin, n_max, index, w=None):
    if mode == "label":
        return pd.Series(np.clip(np.round(pred + margin), 1, n_max).astype(int), index=index)
    if w is None:   # PRISM-LM rule with a log-tolerance margin
        ok = pred <= pred.min(axis=1, keepdims=True) + np.log(SLA_FACTOR) - margin
        return pd.Series(ok.argmax(axis=1) + 1, index=index)
    a, b, _, d = w   # PRISM-LM-J: argmin predicted J; latency normalised by the predicted fixed_N latency
    lat = np.exp(pred)
    rel = lat / lat[:, [-1]]
    ns = np.arange(1, n_max + 1)
    J = a * rel + b * rel * ns / n_max + d * 10 * np.clip(rel / SLA_FACTOR * np.exp(margin) - 1, 0, None)
    return pd.Series(J.argmin(axis=1) + 1, index=index)


def part_b(train, tests, specs, kinds, n_max, folds=5, grow=None):
    from sklearn.model_selection import GroupKFold
    s1 = [c for c in STAGE1_FEATURES if train[c].notna().all()]
    stages = {"stage1": s1, "stage2": s1 + STAGE2_EXTRA}
    Ttr = None
    rows = []
    s1_choice = {}   # Stage 1 choice of each variant on each test set: the count a Stage 2 query starts with
    for stage, cols in stages.items():
        tr = train[stage2_rows(train)] if stage == "stage2" else train
        Ttr = terms(tr, n_max)
        splits = list(GroupKFold(n_splits=folds).split(tr, groups=tr["query"]))
        evs = {name: (te[stage2_rows(te)] if stage == "stage2" else te) for name, te in tests.items()}
        for kind in kinds:
            for mode in ("label", "lm"):
                params = specs[f"{kind}|{mode}|{stage}"]
                oof = [(va, fit_predict(kind, mode, params, tr.iloc[trn], tr.iloc[va], cols, n_max)) for trn, va in splits]
                full = {name: fit_predict(kind, mode, params, tr, ev, cols, n_max) for name, ev in evs.items()}
                for wname, w in NAMED.items():
                    def cv_J(margin, J_rule=False):
                        ch = pd.concat([choose(mode, p, margin, n_max, tr.index[va], w if J_rule else None) for va, p in oof])
                        return J_of(Ttr, ch, w)
                    m_best = min(MARGINS[mode], key=cv_J)
                    variants = [(f"prism{'-lm' if mode == 'lm' else ''}_{kind}_{stage}+margin(J)", m_best, False)]
                    if mode == "lm":
                        m_j = min(MARGINS["lm"], key=lambda m: cv_J(m, True))
                        variants.append((f"prism-lm-J_{kind}_{stage}", m_j, True))
                    for name, ev in evs.items():
                        T = terms(ev, n_max)
                        for pname, mg, jr in variants:
                            ch = choose(mode, full[name], mg, n_max, ev.index, w if jr else None)
                            if stage == "stage1":
                                s1_choice[(kind, mode, wname, jr, name)] = ch
                                res = summary(ev, T, ch, w, n_max, pname)
                            else:
                                start = s1_choice[(kind, mode, wname, jr, name)].loc[ev.index]
                                res = summary_path(ev, start, np.maximum(start, ch), w, n_max, pname, grow[name])
                            rows.append({"test_set": name, "weights": wname, "w": w, "stage": stage, "margin": mg, **res})
        print(f"  part B {stage} done", flush=True)
    # baselines, same weights
    for name, te in tests.items():
        T = terms(te, n_max)
        Ttr = terms(train, n_max)
        for wname, w in NAMED.items():
            for n in range(1, n_max + 1):
                rows.append({"test_set": name, "weights": wname, "w": w, "stage": "-", "margin": np.nan,
                             **summary(te, T, pd.Series(n, index=te.index), w, n_max, f"fixed_{n}e")})
            n_tr = min(range(1, n_max + 1), key=lambda n: J_of(Ttr, pd.Series(n, index=train.index), w))
            rows.append({"test_set": name, "weights": wname, "w": w, "stage": "-", "margin": np.nan,
                         **summary(te, T, pd.Series(n_tr, index=te.index), w, n_max, f"fixed_tuned_J (n={n_tr})")})
            orc = pd.Series([min(range(1, n_max + 1), key=lambda n: float(T[n].loc[i].to_numpy() @ np.array(w, float)))
                             for i in te.index], index=te.index)
            rows.append({"test_set": name, "weights": wname, "w": w, "stage": "-", "margin": np.nan,
                         **summary(te, T, orc, w, n_max, "oracle_J")})
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", type=Path, nargs="+", required=True)
    ap.add_argument("--test", nargs="+", required=True, help="name=sweep_dir[=full_comparison_dir]")
    ap.add_argument("--models", type=Path, required=True, help="manifest.json with tuned hyperparameters")
    ap.add_argument("--kinds", default=",".join(MODEL_TYPES))
    ap.add_argument("--grow", nargs="+", required=True, help="name=growth-path sweep dir (one per test set)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    train, _, n_max, _ = table_of(args.train)
    specs = json.loads((args.models / "manifest.json").read_text())["tuned_params"]
    kinds = [k for k in args.kinds.split(",") if f"{k}|label|stage1" in specs]
    tests, md = {}, ["# Objective J weight sensitivity\n", __doc__.split("Outputs")[0]]
    for spec in args.test:
        parts = spec.split("=")
        tests[parts[0]] = table_of([Path(parts[1])])[0]
        if len(parts) > 2 and (Path(parts[2]) / "executions.csv").exists():
            wins, ranks = part_a(Path(parts[2]), tests[parts[0]], n_max)
            wins.insert(0, "test_set", parts[0]); ranks.insert(0, "test_set", parts[0])
            wins.to_csv(args.out / f"part_a_winners_{parts[0]}.csv", index=False)
            ranks.to_csv(args.out / f"part_a_ranks_{parts[0]}.csv", index=False)
            md += [f"\n## Part A ({parts[0]}): {len(wins)} weight vectors\n",
                   f"PRISM configuration beats every baseline in {100 * wins['prism_beats_all_baselines'].mean():.0f}% of weight vectors. "
                   "Winner family counts: " + str(wins["winner_family"].value_counts().to_dict()) + "\n",
                   wins.groupby("winner_excl_oracle").size().sort_values(ascending=False).head(10).to_frame("weight_vectors_won").to_markdown()]
    grow = {}
    for spec in args.grow:
        name, *dirs = spec.split("=")
        grow[name] = {}
        for d in dirs:
            grow[name].update(grow_medians(Path(d)))
    pb = part_b(train, tests, specs, kinds, n_max, grow=grow)
    pb.to_csv(args.out / "part_b.csv", index=False)
    pd.DataFrame(AUDIT_ROWS).to_csv(args.out / "part_b_query_audit.csv", index=False)
    for name in tests:
        sub = pb[pb["test_set"] == name]
        best = sub.sort_values("J").groupby("weights").head(4)[["weights", "policy", "J", "sla_pct", "core_h", "mean_n", "margin"]]
        md += [f"\n## Part B ({name}): best 4 policies per weight setting (all choices made on training queries)\n",
               best.sort_values(["weights", "J"]).to_markdown(index=False, floatfmt=".3g")]
    (args.out / "report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    sys.exit(main())
