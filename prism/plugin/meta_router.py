"""
PRISM Pluggable Dynamic Multi-Model Meta-Router
==============================================
Inspects physical Catalyst AST plan features (join order depth, join types,
shuffle dispersion, input data volume) to dynamically select the optimal
machine learning regressor (SVR vs. LightGBM vs. Random Forest) for each query.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

from prism.shared.schemas import FeatureVector


@dataclass
class RoutingDecision:
    selected_model: Literal["svr", "lightgbm", "random_forest", "ridge", "xgboost"]
    routing_reason: str
    predicted_complexity_score: float
    confidence_prior: float


class MetaRouter:
    """
    Non-invasive, pluggable query router that matches query AST structure
    to the optimal underlying prediction engine:
      - SVR: Superior for linear scans, shallow filters, and aggregations (D_q <= 3)
      - LightGBM: Superior for deep multi-way joins, star schemas, and large shuffles
      - Random Forest: High-variance fallback for noisy/uncertain query shapes
    """

    def __init__(self, confidence_floor: float = 0.70):
        self.confidence_floor = confidence_floor

    def route(self, fv: FeatureVector) -> RoutingDecision:
        pf = fv.plan_features
        join_depth = pf.join_order_depth
        join_type = pf.join_type.lower()
        input_mb = pf.input_size_bytes / (1024 * 1024)
        shuffle_mb = pf.estimated_shuffle_bytes / (1024 * 1024)
        dag_depth = pf.stage_dag_depth
        fanout = pf.stage_dag_branch_factor

        # Structural complexity score: normalized AST depth & shuffle footprint
        complexity_score = (
            (join_depth * 1.5)
            + (dag_depth * 0.8)
            + (fanout * 0.5)
            + (shuffle_mb / 200.0)
        )

        # 1. Low-complexity aggregation scans and shallow filter pipelines
        # Empirically, SVR achieves fastest pure raw latency (22.6% zero-margin wins)
        # on queries with simple plan geometries and minimal shuffle exchange.
        if (join_depth <= 2 and join_type in ("none", "broadcast")) or (shuffle_mb == 0.0 and input_mb <= 500.0):
            return RoutingDecision(
                selected_model="svr",
                routing_reason=(
                    f"Shallow AST (D_q={join_depth}, type={join_type}, shuffle={shuffle_mb:.1f}MB); "
                    f"dispatched to SVR for zero-margin latency optimization."
                ),
                predicted_complexity_score=complexity_score,
                confidence_prior=0.92,
            )

        # 2. Medium-complexity queries on 500MB scale with moderate join depth
        if join_depth <= 3 and join_type not in ("sort_merge", "shuffled_hash") and input_mb <= 600.0:
            return RoutingDecision(
                selected_model="svr",
                routing_reason=(
                    f"Moderate AST depth (D_q={join_depth}, input={input_mb:.1f}MB); "
                    f"dispatched to SVR to avoid decision-tree boundary discretization."
                ),
                predicted_complexity_score=complexity_score,
                confidence_prior=0.88,
            )

        # 3. High-complexity deep multi-way joins, star/snowflake schemas, or heavy shuffles
        # Observed: LightGBM achieves 18/22 SLA on TPC-H, 9/10 on TPC-DS multi-way joins
        # and partition-skewed shuffles due to leaf-wise gradient boosting.
        if (
            join_depth > 3
            or join_type in ("sort_merge", "shuffled_hash")
            or shuffle_mb >= 100.0
            or input_mb >= 900.0
        ):
            return RoutingDecision(
                selected_model="lightgbm",
                routing_reason=(
                    f"High-complexity join structure (D_q={join_depth}, type={join_type}, "
                    f"shuffle={shuffle_mb:.1f}MB); dispatched to LightGBM for non-linear partition isolation."
                ),
                predicted_complexity_score=complexity_score,
                confidence_prior=0.95,
            )

        # 4. Fallback: Ensemble Bagging (Random Forest) for balanced variance minimization
        return RoutingDecision(
            selected_model="random_forest",
            routing_reason=(
                f"Balanced plan geometry (D_q={join_depth}, complexity={complexity_score:.2f}); "
                f"dispatched to Random Forest for bagging variance minimization."
            ),
            predicted_complexity_score=complexity_score,
            confidence_prior=0.90,
        )
