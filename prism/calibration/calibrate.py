"""
PRISM Contention-Aware Calibration Engine Module
================================================
Implements Contract 3 pure calibration function logic.
"""
from __future__ import annotations
import math
from prism.shared.schemas import (
    CalibrationInput,
    CalibrationOutput,
    CalibratedRecommendation,
)

CONFIDENCE_THRESHOLD = 0.5
CAPACITY_SAFETY_MARGIN = 0.9


def _proportional_fallback(predicted_memory_mb: int, available_executors: int) -> CalibratedRecommendation:
    num_executors = max(1, min(available_executors, 2))
    return CalibratedRecommendation(
        num_executors=num_executors,
        executor_cores=1,
        executor_memory_mb=min(predicted_memory_mb, 2048),
    )


def calibrate(inp: CalibrationInput) -> CalibrationOutput:
    if inp.confidence < CONFIDENCE_THRESHOLD:
        fallback = _proportional_fallback(
            inp.predicted_executor_memory_mb, inp.cluster_load.available_executors
        )
        return CalibrationOutput(
            calibrated=fallback,
            used_fallback=True,
            reason=f"confidence {inp.confidence:.2f} below threshold {CONFIDENCE_THRESHOLD}",
        )

    safe_capacity = int(inp.cluster_load.available_executors * CAPACITY_SAFETY_MARGIN)
    if inp.predicted_num_executors > safe_capacity:
        capped = max(1, safe_capacity)
        return CalibrationOutput(
            calibrated=CalibratedRecommendation(
                num_executors=capped,
                executor_cores=inp.predicted_executor_cores,
                executor_memory_mb=inp.predicted_executor_memory_mb,
            ),
            used_fallback=True,
            reason=(
                f"predicted {inp.predicted_num_executors} executors exceeds "
                f"safe capacity {safe_capacity} (available={inp.cluster_load.available_executors})"
            ),
        )

    return CalibrationOutput(
        calibrated=CalibratedRecommendation(
            num_executors=inp.predicted_num_executors,
            executor_cores=inp.predicted_executor_cores,
            executor_memory_mb=inp.predicted_executor_memory_mb,
        ),
        used_fallback=False,
        reason=None,
    )


def calibrate_contention_aware(inp: CalibrationInput, total_executors: int, total_cores: int) -> CalibrationOutput:
    """Calibration v3, following the proposal's C4 wording (rule fixed 2026-10-25 10:40, post-hoc: designed after the
    original calibrate() was seen to fail under CPU contention; calibrate() itself is unchanged).

    inp.cluster_load.available_executors = executor slots the cluster can still grant (supply);
    inp.cluster_load.available_cores     = CPU cores not taken by co-located load (contention signal).
      1. never recommend more executors than the cluster can supply (no 0.9 margin: on 4 slots it cost a whole executor);
      2. "degrade gracefully - larger allocations": when co-located load takes CPU, scale the prediction up by the
         CPU pressure rho = total_cores / free_cores (parameter-free; rho = 1 on an idle cluster -> prediction unchanged);
      3. if even the full supply is below n x rho, keep the supply and report it ("relaxed SLA expectations").
    Low confidence -> the same proportional fallback as calibrate().
    """
    if inp.confidence < CONFIDENCE_THRESHOLD:
        return calibrate(inp)
    supply = max(1, min(total_executors, inp.cluster_load.available_executors))
    free_cores = max(inp.predicted_executor_cores, min(total_cores, inp.cluster_load.available_cores))
    rho = total_cores / free_cores
    wanted = math.ceil(inp.predicted_num_executors * rho - 1e-9)
    n = max(1, min(supply, wanted))
    reason = None
    if n != inp.predicted_num_executors or wanted > supply:
        reason = f"cpu pressure {rho:.2f}: predicted {inp.predicted_num_executors} -> {n} (supply {supply})"
        if wanted > supply:
            reason += "; SLA at risk (supply below contention-scaled need)"
    return CalibrationOutput(
        calibrated=CalibratedRecommendation(
            num_executors=n,
            executor_cores=inp.predicted_executor_cores,
            executor_memory_mb=inp.predicted_executor_memory_mb,
        ),
        used_fallback=n != inp.predicted_num_executors,
        reason=reason,
    )
