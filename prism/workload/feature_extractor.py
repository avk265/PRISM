"""
PRISM Catalyst Feature Extractor Module
=======================================
Parses physical Spark Catalyst execution plans to produce Contract 1 FeatureVector objects.
"""
from __future__ import annotations
from prism.shared.schemas import (
    FeatureVector,
    PlanFeatures,
    ClusterLoadFeatures,
    AqeCorrection,
)
from .cluster_monitor import get_cluster_load


def _count_joins(plan_str: str) -> tuple[str, int]:
    join_type = "none"
    if "BroadcastHashJoin" in plan_str:
        join_type = "broadcast"
    elif "SortMergeJoin" in plan_str:
        join_type = "sort_merge"
    elif "ShuffledHashJoin" in plan_str:
        join_type = "shuffled_hash"
    depth = plan_str.count("Join")
    return join_type, depth


def _estimate_shuffle_bytes(df) -> float:
    try:
        stats = df._jdf.queryExecution().optimizedPlan().stats()
        return float(stats.sizeInBytes().toString())
    except Exception:
        return 100000000.0  # 100 MB reasonable default


def _stage_dag_shape(df) -> tuple[int, int]:
    try:
        plan_str = df._jdf.queryExecution().sparkPlan().toString()
    except Exception:
        try:
            plan_str = df._jdf.queryExecution().executedPlan().toString()
        except Exception:
            return 3, 2
    lines = [l for l in plan_str.split("\n") if l.strip()]
    indents = [len(l) - len(l.lstrip(" :+-")) for l in lines]
    depth = max(indents) // 3 if indents else 2
    from collections import Counter
    branch_factor = max(Counter(indents).values()) if indents else 1
    return max(depth, 1), branch_factor


def extract_submission_features(df, spark, query_id: str, raw_sql: str = "", data_dir=None) -> FeatureVector:
    try:
        plan_str = df._jdf.queryExecution().sparkPlan().toString()
    except Exception:
        plan_str = ""

    join_type, join_depth = _count_joins(plan_str)
    if join_depth == 0 and raw_sql:
        join_depth = raw_sql.lower().count("join")

    depth, branch = _stage_dag_shape(df)

    # Compute physical table input size from disk table files if data_dir provided
    input_size = 0.0
    if data_dir is not None:
        from pathlib import Path
        data_path = Path(data_dir)
        if data_path.exists():
            sql_clean = (raw_sql.lower() + " " + plan_str.lower())
            for item in data_path.iterdir():
                tbl_name = item.stem if item.is_file() else item.name
                if tbl_name.lower() in sql_clean:
                    if item.is_file():
                        input_size += float(item.stat().st_size)
                    elif item.is_dir() and not item.name.startswith("."):
                        dir_sz = sum(f.stat().st_size for f in item.glob("**/*") if f.is_file())
                        input_size += float(dir_sz)

    if input_size <= 0.0:
        try:
            stats_bytes = float(df._jdf.queryExecution().optimizedPlan().stats().sizeInBytes().toString())
            if stats_bytes < 1e12:
                input_size = stats_bytes
            else:
                input_size = 50000000.0
        except Exception:
            input_size = 50000000.0

    # Calculate estimated shuffle bytes directly from physical plan exchange nodes and table input sizes.
    # With AQE on, sparkPlan() has no Exchange nodes (they are inserted later), so count them in
    # executedPlan(), whose initial AQE plan contains them; otherwise this feature is always 0.
    try:
        exec_str = df._jdf.queryExecution().executedPlan().toString()
    except Exception:
        exec_str = plan_str
    num_shuffles = exec_str.count("Exchange")
    if num_shuffles == 0:
        shuffle_bytes = 0.0
    else:
        # Sum size of shuffled non-broadcast join inputs
        shuffle_bytes = input_size if join_depth > 0 else (input_size * 0.1)

    load = get_cluster_load(spark)

    return FeatureVector(
        query_id=query_id,
        stage="submission",
        plan_features=PlanFeatures(
            input_size_bytes=input_size,
            join_type=join_type,
            join_order_depth=join_depth,
            estimated_shuffle_bytes=shuffle_bytes,
            stage_dag_depth=depth,
            stage_dag_branch_factor=branch,
        ),
        cluster_load_features=ClusterLoadFeatures(**load),
        aqe_correction=AqeCorrection(),
    )


def extract_aqe_features(
    submission_features: FeatureVector,
    true_post_shuffle_bytes: float,
    true_partition_count: int,
) -> FeatureVector:
    updated = submission_features.model_copy(deep=True)
    updated.stage = "aqe_checkpoint"
    updated.aqe_correction = AqeCorrection(
        true_post_shuffle_bytes=true_post_shuffle_bytes,
        true_partition_count=true_partition_count,
    )
    return updated
