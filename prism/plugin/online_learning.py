"""
PRISM Pluggable Continuous Online Learning & Drift Adaptation Plugin
====================================================================
Collects runtime physical execution telemetry (wall-clock latency, JVM duration,
GC overhead, true post-shuffle volume, CPU allocation waste) into a thread-safe
reservoir buffer.

Detects data distribution drift via running statistical discrepancy tests and
dynamically computes incremental calibration weights (W_online) to adapt resource
predictions to workload shifts without offline model retraining.
"""
from __future__ import annotations
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class QueryTelemetryRecord:
    query_id: str
    workload: str
    timestamp: float
    estimated_shuffle_bytes: float
    true_post_shuffle_bytes: float
    allocated_executors: int
    allocated_cores: int
    allocated_memory_mb: int
    measured_latency_s: float
    measured_cpu_waste_h: float
    measured_gc_ms: float
    sla_target_s: float
    sla_met: bool


@dataclass
class DriftDetectionResult:
    is_drift_detected: bool
    drift_score: float
    sample_count: int
    mean_shuffle_error: float
    variance_shuffle_error: float
    adaptation_weight: float
    recommended_action: str


class OnlineDriftAdaptationPlugin:
    """
    Continuous Online Learning & Warm-Start Drift Adaptation Plugin.
    Non-invasively attaches to query completion events to maintain
    online model freshness.
    """

    def __init__(
        self,
        reservoir_capacity: int = 128,
        drift_z_threshold: float = 1.645,  # 90% confidence Z-score
        adaptation_rate: float = 0.25,
    ):
        self.capacity = reservoir_capacity
        self.drift_z_threshold = drift_z_threshold
        self.adaptation_rate = adaptation_rate
        self.buffer: deque[QueryTelemetryRecord] = deque(maxlen=reservoir_capacity)
        
        # Baseline statistics (computed from historical baseline)
        self.baseline_mean_error: float = 0.0
        self.baseline_std_error: float = 1.0
        self.baseline_samples: int = 0
        
        # Dynamic online multipliers
        self.online_executor_multiplier: float = 1.0
        self.online_memory_multiplier: float = 1.0
        self.total_observations: int = 0

    def initialize_baseline(self, historical_errors: List[float]):
        """
        Initializes historical baseline distribution parameters from empirical runs.
        """
        if historical_errors:
            arr = np.array(historical_errors, dtype=np.float64)
            self.baseline_mean_error = float(np.mean(arr))
            self.baseline_std_error = max(float(np.std(arr)), 1e-4)
            self.baseline_samples = len(arr)

    def record_telemetry(self, record: QueryTelemetryRecord) -> DriftDetectionResult:
        """
        Ingests a query's physical execution telemetry into the reservoir buffer
        and evaluates data distribution drift.
        """
        self.buffer.append(record)
        self.total_observations += 1

        # Compute relative shuffle estimation error:
        # delta = (S_true - S_est) / max(S_est, 1)
        denom = max(record.estimated_shuffle_bytes, 1.0)
        curr_error = (record.true_post_shuffle_bytes - record.estimated_shuffle_bytes) / denom

        # If baseline is empty, incrementally accumulate initial statistics
        if self.baseline_samples < 10:
            self.baseline_mean_error += (curr_error - self.baseline_mean_error) / max(self.total_observations, 1)
            self.baseline_samples += 1
            return DriftDetectionResult(
                is_drift_detected=False,
                drift_score=0.0,
                sample_count=len(self.buffer),
                mean_shuffle_error=curr_error,
                variance_shuffle_error=0.0,
                adaptation_weight=1.0,
                recommended_action="Accumulating initial baseline telemetry observations.",
            )

        # Compute rolling window statistics over the reservoir buffer
        window_errors = [
            (r.true_post_shuffle_bytes - r.estimated_shuffle_bytes) / max(r.estimated_shuffle_bytes, 1.0)
            for r in self.buffer
        ]
        window_arr = np.array(window_errors, dtype=np.float64)
        window_mean = float(np.mean(window_arr))
        window_std = max(float(np.std(window_arr)), 1e-4)

        # Standardized Z-Score Drift Metric:
        # Z = |mu_window - mu_baseline| / (sigma_baseline / sqrt(N_window))
        n_window = len(window_arr)
        std_err = self.baseline_std_error / math.sqrt(n_window)
        drift_score = abs(window_mean - self.baseline_mean_error) / max(std_err, 1e-4)

        is_drift = drift_score >= self.drift_z_threshold

        if is_drift:
            # If true shuffle volume consistently exceeds estimate (positive drift),
            # adaptively increase the online executor and memory multipliers:
            # Multiplier updates proportionally to error deviation
            adjustment = np.clip(window_mean * self.adaptation_rate, -0.30, 0.50)
            self.online_executor_multiplier = round(float(1.0 + adjustment), 4)
            self.online_memory_multiplier = round(float(1.0 + max(0.0, adjustment * 0.8)), 4)
            action = (
                f"Statistical drift detected (Z={drift_score:.2f} >= {self.drift_z_threshold:.2f}). "
                f"Applied warm-start calibration multipliers: Exec={self.online_executor_multiplier}x, "
                f"Mem={self.online_memory_multiplier}x."
            )
        else:
            # Exponentially decay multipliers back to 1.0 when drift stabilizes
            self.online_executor_multiplier = round(
                float(self.online_executor_multiplier * 0.95 + 1.0 * 0.05), 4
            )
            self.online_memory_multiplier = round(
                float(self.online_memory_multiplier * 0.95 + 1.0 * 0.05), 4
            )
            action = f"Stable distribution (Z={drift_score:.2f} < {self.drift_z_threshold:.2f}); baseline calibration nominal."

        return DriftDetectionResult(
            is_drift_detected=is_drift,
            drift_score=round(drift_score, 4),
            sample_count=len(self.buffer),
            mean_shuffle_error=round(window_mean, 4),
            variance_shuffle_error=round(float(np.var(window_arr)), 6),
            adaptation_weight=self.online_executor_multiplier,
            recommended_action=action,
        )

    def adapt_recommendation(self, num_executors: int, memory_mb: int) -> tuple[int, int, float]:
        """
        Applies warm-start drift adaptation multipliers to incoming predictions.
        """
        adapted_exec = max(1, min(16, int(round(num_executors * self.online_executor_multiplier))))
        adapted_mem = max(512, int(round(memory_mb * self.online_memory_multiplier)))
        return adapted_exec, adapted_mem, self.online_executor_multiplier
