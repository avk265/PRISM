"""
Select ONE PRISM configuration before testing (idle cluster), using the training queries only.

Candidates: the 12 deployed configurations (6 learners x {PRISM-C, PRISM-L}) with the hyperparameters and safety
margins stored in the model manifest. Criterion: the objective J of Eq. (1) (alpha = beta = gamma = delta = 1),
averaged over grouped 5-fold cross-validation on the training queries. Each held-out training query is scored with
its measured median run at the Stage 1 count the configuration chooses; Stage 1 decisions are fixed before the query
starts, so every score is a measured execution. Ties (|dJ| < 1e-9) go to the lower mean core-hours.
No test query is read. Output: <models>/selected_idle.json
Run: venv/bin/python -I prism/model/select_config.py --train <sweep> [<sweep> ...] --models prism/model/expanded_training
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from prism.model.train_from_sweep import STAGE1_FEATURES, MODEL_TYPES
from prism.evaluation.full_comparison import table_of
from prism.evaluation.objective_sensitivity import fit_predict, choose, terms, J_of

W = (1, 1, 1, 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", type=Path, nargs="+", required=True)
    ap.add_argument("--models", type=Path, required=True)
    ap.add_argument("--folds", type=int, default=5)
    args = ap.parse_args(argv)
    train, _, n_max, _ = table_of(args.train)
    man = json.loads((args.models / "manifest.json").read_text())
    specs, margins = man["tuned_params"], man.get("safety_margins", {})
    cols = [c for c in STAGE1_FEATURES if train[c].notna().all()]
    T = terms(train, n_max)
    splits = list(GroupKFold(n_splits=args.folds).split(train, groups=train["query"]))
    rows = []
    for kind in [k for k in MODEL_TYPES if f"{k}|label|stage1" in specs]:
        for mode in ("label", "lm"):
            m = margins.get(f"{kind}|{mode}|stage1", 0.0)
            ch = pd.concat([choose(mode, fit_predict(kind, mode, specs[f"{kind}|{mode}|stage1"], train.iloc[tr],
                                                     train.iloc[va], cols, n_max), m, n_max, train.index[va])
                            for tr, va in splits])
            core = float(np.mean([train.at[i, f"coreh_{int(n)}"] for i, n in ch.items()]))
            sla = float(np.mean([train.at[i, f"lat_{int(n)}"] <= 1.15 * train.at[i, f"lat_{n_max}"] for i, n in ch.items()]))
            rows.append({"kind": kind, "mode": mode, "margin": m, "cv_J": J_of(T, ch, W), "cv_sla_pct": 100 * sla,
                         "cv_core_h_mean": core})
            print(f"  {kind:13s} {mode:5s} J={rows[-1]['cv_J']:.4f} SLA={100 * sla:.1f}%", flush=True)
    r = pd.DataFrame(rows).sort_values(["cv_J", "cv_core_h_mean"]).reset_index(drop=True)
    best = r.iloc[0]
    out = {"criterion": "mean objective J (weights 1,1,1,1), grouped 5-fold CV on training queries, Stage 1 decision",
           "train_sweeps": [str(p) for p in args.train], "n_train_queries": int(len(train)),
           "selected": {"kind": best.kind, "mode": best["mode"], "margin": float(best.margin)},
           "candidates": r.to_dict("records")}
    (args.models / "selected_idle.json").write_text(json.dumps(out, indent=2))
    print(r.to_string(index=False))
    print(f"selected: {best.kind} {best['mode']}")


if __name__ == "__main__":
    sys.exit(main())
