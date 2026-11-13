"""
PRISM Model Training Engine Module
===================================
Trains Stage 1 and Stage 2 models from sweep logs.
Supports multiple model types: random_forest, xgboost, lightgbm, ridge, svr.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error

ModelType = Literal["random_forest", "xgboost", "lightgbm", "ridge", "svr"]

FEATURE_COLUMNS_STAGE1 = [
    "input_size_bytes", "join_order_depth", "estimated_shuffle_bytes",
    "stage_dag_depth", "stage_dag_branch_factor",
    "queue_depth", "available_executors", "available_cores", "colocated_job_count",
]
FEATURE_COLUMNS_STAGE2 = FEATURE_COLUMNS_STAGE1 + [
    "true_post_shuffle_bytes", "true_partition_count",
]
TARGET_COLUMNS = ["num_executors", "executor_cores", "executor_memory_mb"]

ALL_MODEL_TYPES: list[ModelType] = [
    "random_forest", "xgboost", "lightgbm", "ridge", "svr"
]


from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def _build_model(model_type: ModelType):
    """Construct an unfitted sklearn-compatible multi-output regression model."""
    if model_type == "random_forest":
        return RandomForestRegressor(
            n_estimators=250, min_samples_leaf=2, random_state=42, n_jobs=-1
        )
    elif model_type == "xgboost":
        from xgboost import XGBRegressor
        base = XGBRegressor(
            n_estimators=250, max_depth=5, learning_rate=0.08,
            random_state=42, n_jobs=-1, verbosity=0,
        )
        return MultiOutputRegressor(base)
    elif model_type == "lightgbm":
        from lightgbm import LGBMRegressor
        base = LGBMRegressor(
            n_estimators=300, num_leaves=15, min_child_samples=5, learning_rate=0.05,
            random_state=42, n_jobs=-1, verbose=-1,
        )
        return MultiOutputRegressor(base)
    elif model_type == "ridge":
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=10.0)),
        ])
        return MultiOutputRegressor(pipe)
    elif model_type == "svr":
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("svr", SVR(kernel="rbf", C=10.0)),
        ])
        return MultiOutputRegressor(pipe)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def load_sweep_log(path: Path) -> pd.DataFrame:
    raw_rows = []
    with open(path) as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            rec = json.loads(line_str)
            if not rec.get("success"):
                continue
            cfg = rec.get("config", {})
            lat = float(rec.get("latency_s", 0.0))
            e = int(cfg.get("num_executors", 2))
            c = int(cfg.get("executor_cores", 2))
            m = int(cfg.get("executor_memory_mb", 2048))
            q_base = rec.get("app_name", "q_unknown").split("_")[0]
            scale = rec.get("dataset_scale", "")
            query_template = f"{q_base}_{scale}" if scale else q_base
            bg_load = rec.get("background_load", "none")

            row = {
                "query_template": query_template,
                "background_load": bg_load,
                "latency_s": lat,
                "num_executors": e,
                "executor_cores": c,
                "executor_memory_mb": m,
            }
            for col in FEATURE_COLUMNS_STAGE2:
                if col in rec:
                    row[col] = rec[col]
            raw_rows.append(row)

    df_raw = pd.DataFrame(raw_rows)

    # Compute static baseline latency T_static per (query_template, background_load)
    static_lats = {}
    for (q, load), sub in df_raw.groupby(["query_template", "background_load"]):
        st = sub[(sub["num_executors"] == 4) & (sub["executor_cores"] == 2) & (sub["executor_memory_mb"] == 4096)]
        if not st.empty:
            static_lats[(q, load)] = float(st["latency_s"].iloc[0])
        else:
            static_lats[(q, load)] = float(sub["latency_s"].mean())

    # Calculate exact normalized C2 J-score for each trial
    j_scores = []
    for _, r in df_raw.iterrows():
        t_stat = static_lats.get((r["query_template"], r["background_load"]), 15.0)
        norm_lat = r["latency_s"] / max(t_stat, 1e-4)
        r_alloc = (r["num_executors"] * r["executor_cores"] * r["latency_s"]) / 3600.0
        r_static = (4 * 2 * t_stat) / 3600.0
        norm_r = r_alloc / max(r_static, 1e-8)
        
        eta_cpu = 0.85
        if r.get("estimated_shuffle_bytes", 0.0) > 0:
            s_bytes = float(r["estimated_shuffle_bytes"])
            eta_cpu -= 0.08 * (s_bytes / (1e8 + s_bytes))
        if r["background_load"] != "none":
            eta_cpu -= 0.05
        eta_cpu = max(0.65, min(0.92, eta_cpu))
        
        cpu_waste = max(0.000001, r_alloc * (1.0 - eta_cpu))
        norm_waste = cpu_waste / max(r_static, 1e-8)
        
        target_sla = 1.15 * t_stat
        sla_penalty = max(0.0, r["latency_s"] - target_sla) / max(t_stat, 1e-4)
        j = 0.4 * norm_lat + 0.3 * norm_r + 0.2 * norm_waste + 0.1 * sla_penalty
        j_scores.append(j)

    df_raw["j_score"] = j_scores
    # Filter for minimum J-score config for each (query_template, background_load)
    best_indices = df_raw.groupby(["query_template", "background_load"])["j_score"].idxmin()
    return df_raw.loc[best_indices].reset_index(drop=True)


def compute_j_loss(df_sub: pd.DataFrame, pred: np.ndarray, alpha=0.4, beta=0.3, gamma=0.2, delta=0.1) -> float:
    pred_exec = np.clip(pred[:, 0], 1, 8)
    pred_cores = np.clip(pred[:, 1], 1, 4)
    pred_mem = np.clip(pred[:, 2], 512, 8192)
    latencies = df_sub["latency_s"].values
    
    r_alloc = (pred_exec * pred_cores * latencies) / 3600.0
    r_gt = (df_sub["num_executors"].values * df_sub["executor_cores"].values * latencies) / 3600.0
    r_static = (4 * 2 * latencies) / 3600.0
    
    eta_cpu = 0.85
    r_useful = eta_cpu * np.minimum(r_alloc, r_gt)
    cpu_waste = np.maximum(0.000001, r_alloc - r_useful)
    
    norm_lat = 1.0  # evaluated on split
    norm_r = r_alloc / np.maximum(r_static, 1e-8)
    norm_waste = cpu_waste / np.maximum(r_static, 1e-8)
    sla_penalty = np.maximum(0.0, latencies - 1.15 * latencies) / np.maximum(latencies, 1e-4)
    
    j_losses = alpha * norm_lat + beta * norm_r + gamma * norm_waste + delta * sla_penalty
    return float(np.mean(j_losses))


def train_stage1(df: pd.DataFrame, out_dir: Path, model_type: ModelType = "random_forest"):
    for col in FEATURE_COLUMNS_STAGE1:
        if col not in df.columns:
            df[col] = 0.0

    groups = df["query_template"]
    X = df[FEATURE_COLUMNS_STAGE1].fillna(0.0)
    y = df[TARGET_COLUMNS]

    gkf = GroupKFold(n_splits=min(4, groups.nunique()))
    maes, j_losses = [], []
    for train_idx, test_idx in gkf.split(X, y, groups):
        model = _build_model(model_type)
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(X.iloc[test_idx])
        if pred.ndim == 1:
            pred = pred.reshape(-1, 3)
        maes.append(mean_absolute_error(y.iloc[test_idx], pred))
        j_losses.append(compute_j_loss(df.iloc[test_idx], pred))

    print(f"Stage-1 [{model_type}] GroupKFold MAE: {np.mean(maes):.3f} | Multi-Objective J Loss: {np.mean(j_losses):.3f}")

    final_model = _build_model(model_type)
    final_model.fit(X, y)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_name = f"stage1_{model_type}.joblib" if model_type != "random_forest" else "stage1_model.joblib"
    joblib.dump({"model": final_model, "feature_columns": FEATURE_COLUMNS_STAGE1,
                 "target_columns": TARGET_COLUMNS, "version": f"stage1-{model_type}-v1.0",
                 "model_type": model_type},
                out_dir / artifact_name)
    print(f"Saved {out_dir / artifact_name}")
    return {"mae": float(np.mean(maes)), "j_loss": float(np.mean(j_losses))}


def train_stage2(df: pd.DataFrame, out_dir: Path, model_type: ModelType = "random_forest"):
    for col in FEATURE_COLUMNS_STAGE2:
        if col not in df.columns:
            df[col] = 0.0

    groups = df["query_template"]
    X = df[FEATURE_COLUMNS_STAGE2].fillna(0.0)
    y = df[TARGET_COLUMNS]

    gkf = GroupKFold(n_splits=min(4, groups.nunique()))
    maes, j_losses = [], []
    for train_idx, test_idx in gkf.split(X, y, groups):
        model = _build_model(model_type)
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(X.iloc[test_idx])
        if pred.ndim == 1:
            pred = pred.reshape(-1, 3)
        maes.append(mean_absolute_error(y.iloc[test_idx], pred))
        j_losses.append(compute_j_loss(df.iloc[test_idx], pred))

    print(f"Stage-2 [{model_type}] GroupKFold MAE: {np.mean(maes):.3f} | Multi-Objective J Loss: {np.mean(j_losses):.3f}")

    final_model = _build_model(model_type)
    final_model.fit(X, y)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_name = f"stage2_{model_type}.joblib" if model_type != "random_forest" else "stage2_model.joblib"
    joblib.dump({"model": final_model, "feature_columns": FEATURE_COLUMNS_STAGE2,
                 "target_columns": TARGET_COLUMNS, "version": f"stage2-{model_type}-v1.0",
                 "model_type": model_type},
                out_dir / artifact_name)
    print(f"Saved {out_dir / artifact_name}")
    return {"mae": float(np.mean(maes)), "j_loss": float(np.mean(j_losses))}


def train_all_models(sweep_log_path: Path, out_dir: Path) -> dict:
    """Train all model types on the same sweep data and return cross-val metrics."""
    df = load_sweep_log(sweep_log_path)
    print(f"Loaded {len(df)} optimal-config rows from sweep log")
    
    results = {}
    for mt in ALL_MODEL_TYPES:
        print(f"\n{'='*60}")
        print(f"Training model type: {mt}")
        print(f"{'='*60}")
        try:
            s1 = train_stage1(df.copy(), out_dir, model_type=mt)
            s2 = train_stage2(df.copy(), out_dir, model_type=mt)
            results[mt] = {"stage1": s1, "stage2": s2, "status": "ok"}
        except Exception as e:
            print(f"  FAILED to train {mt}: {e}")
            results[mt] = {"status": "error", "error": str(e)}
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train PRISM Stage 1 and Stage 2 models")
    parser.add_argument("--sweep-log", type=str, default="person-b-model/sweep/sweep_log.jsonl")
    parser.add_argument("--out-dir", type=str, default="prism/model/baseline_models")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    sweep_path = project_root / args.sweep_log
    out_dir = project_root / args.out_dir

    print(f"Training all models using {sweep_path}")
    print(f"Output directory: {out_dir}")
    train_all_models(sweep_path, out_dir)
