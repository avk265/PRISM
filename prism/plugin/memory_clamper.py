"""
PRISM Pluggable Contention-Aware Dynamic Memory Clamper
======================================================
Reads live host system memory state from `/proc/meminfo` and cluster
contention metrics to dynamically clamp executor memory boundaries under
concurrent background thread contention (K >= 2).

Prevents OS page cache thrashing, dirty page flush stalls, and memory
bus saturation under high-contention multi-tenant workloads.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryClampingResult:
    original_memory_mb: int
    clamped_memory_mb: int
    system_available_mb: float
    dirty_page_ratio: float
    is_clamped: bool
    clamping_reason: str


class ContentionMemoryClamper:
    """
    Computes dynamic memory clamping from live Linux /proc/meminfo and
    cluster co-location counters (K_colocated).
    """

    def __init__(self, memory_safety_margin: float = 0.85, min_executor_memory_mb: int = 1024):
        self.memory_safety_margin = memory_safety_margin
        self.min_executor_memory_mb = min_executor_memory_mb

    def read_system_meminfo(self) -> tuple[float, float, float]:
        """
        Reads actual physical memory statistics from Linux /proc/meminfo.
        Returns:
            (mem_total_mb, mem_available_mb, dirty_page_ratio)
        """
        mem_total_kb = 16 * 1024 * 1024  # 16GB fallback if not on Linux
        mem_avail_kb = 8 * 1024 * 1024
        dirty_kb = 0.0

        if os.path.exists("/proc/meminfo"):
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val_parts = parts[1].strip().split()
                            val_kb = float(val_parts[0]) if val_parts else 0.0
                            if key == "MemTotal":
                                mem_total_kb = val_kb
                            elif key == "MemAvailable":
                                mem_avail_kb = val_kb
                            elif key == "Dirty":
                                dirty_kb = val_kb
            except Exception:
                pass

        mem_total_mb = mem_total_kb / 1024.0
        mem_avail_mb = mem_avail_kb / 1024.0
        dirty_ratio = dirty_kb / max(mem_avail_kb, 1.0)
        return mem_total_mb, mem_avail_mb, dirty_ratio

    def clamp_memory(
        self,
        predicted_memory_mb: int,
        num_executors: int,
        colocated_jobs: int = 0,
    ) -> MemoryClampingResult:
        """
        Calculates contention-aware memory boundary:
            M_avail_budget = (mem_available_mb * safety_margin) / (colocated_jobs + 1)
            M_per_exec_cap = M_avail_budget / num_executors
            M_clamped = max(min_mem, min(predicted_mem, M_per_exec_cap))
        """
        mem_total_mb, mem_avail_mb, dirty_ratio = self.read_system_meminfo()

        # Compute dynamic contention divisor from active colocated processes
        contention_factor = max(1, colocated_jobs + 1)

        # Calculate safe per-executor memory headroom
        safe_cluster_headroom = mem_avail_mb * self.memory_safety_margin
        safe_job_headroom = safe_cluster_headroom / contention_factor
        safe_per_exec_mb = max(
            self.min_executor_memory_mb,
            int(safe_job_headroom / max(1, num_executors))
        )

        # If dirty page ratio is high (> 10%), reduce memory ceiling by another 15%
        # to prevent Linux pdflush/kswapd writeback stalls
        if dirty_ratio > 0.10:
            safe_per_exec_mb = int(safe_per_exec_mb * 0.85)

        is_clamped = predicted_memory_mb > safe_per_exec_mb
        clamped_mb = min(predicted_memory_mb, safe_per_exec_mb) if is_clamped else predicted_memory_mb
        clamped_mb = max(self.min_executor_memory_mb, clamped_mb)

        if is_clamped:
            reason = (
                f"Contention K={colocated_jobs} with {mem_avail_mb:.0f}MB available RAM; "
                f"clamped from {predicted_memory_mb}MB to {clamped_mb}MB "
                f"(dirty ratio={dirty_ratio:.2%}) to avoid memory bus thrashing."
            )
        else:
            reason = "Allocated memory within safe host memory budget."

        return MemoryClampingResult(
            original_memory_mb=predicted_memory_mb,
            clamped_memory_mb=clamped_mb,
            system_available_mb=mem_avail_mb,
            dirty_page_ratio=dirty_ratio,
            is_clamped=is_clamped,
            clamping_reason=reason,
        )
