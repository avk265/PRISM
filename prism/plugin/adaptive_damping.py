"""
PRISM Pluggable Dynamic Fan-Out Adaptive AQE Damping
===================================================
Replaces static beta = 0.50 in Algorithm 2 with a dynamic damping factor
scaled by the physical DAG stage branch factor (fan-out):
    beta(Phi_fanout) = min(0.85, 0.40 + 0.15 * Phi_fanout)
Wide fan-out stages with concurrent shuffle writes scale up more aggressively
to absorb intermediate partition explosions and eliminate disk spill.
"""
from __future__ import annotations
import math


class DynamicAqeDamping:
    """
    Computes dynamic adaptive damping factor for Stage-2 AQE corrective reallocation.
    """

    def __init__(self, beta_base: float = 0.40, beta_scale: float = 0.15, beta_max: float = 0.85):
        self.beta_base = beta_base
        self.beta_scale = beta_scale
        self.beta_max = beta_max

    def compute_beta(self, dag_branch_factor: int) -> float:
        """
        Calculates dynamic beta from physical stage DAG branch factor (fan-out).
        """
        fanout = max(1, dag_branch_factor)
        beta = min(self.beta_max, self.beta_base + self.beta_scale * fanout)
        return round(beta, 4)

    def compute_reallocation(
        self,
        current_executors: int,
        estimated_shuffle_bytes: float,
        true_post_shuffle_bytes: float,
        dag_branch_factor: int,
    ) -> tuple[int, float, float]:
        """
        Computes the corrected executor count using dynamic damping:
            delta_shuffle = (true_post_shuffle_bytes - estimated_shuffle_bytes) / max(estimated, 1)
            N_exec^(k+1) = ceil(N_exec^(k) * (1 + beta(Phi_fanout) * delta_shuffle))
        Returns:
            (reallocated_executors, dynamic_beta, delta_shuffle)
        """
        denom = max(estimated_shuffle_bytes, 1.0)
        delta_shuffle = (true_post_shuffle_bytes - estimated_shuffle_bytes) / denom
        beta = self.compute_beta(dag_branch_factor)

        # Apply damped scaling factor
        scale_multiplier = 1.0 + (beta * delta_shuffle)
        # Prevent contraction below 1 executor or runaway scaling above 16
        new_exec = max(1, min(16, math.ceil(current_executors * scale_multiplier)))

        return new_exec, beta, round(delta_shuffle, 4)
