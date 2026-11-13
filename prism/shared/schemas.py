"""
PRISM Unified Pydantic Schemas
==============================
Defines the strict interfaces across PRISM modules (Contracts 1, 2, and 3).
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

# ----------------- Contract 1: Feature Schema -----------------

class PlanFeatures(BaseModel):
    input_size_bytes: float = Field(..., ge=0, description="Optimized logical plan estimated size in bytes")
    join_type: Literal["broadcast", "sort_merge", "shuffled_hash", "none", "other_join"] = Field(
        ..., description="Dominant join algorithm extracted from Catalyst physical plan"
    )
    join_order_depth: int = Field(..., ge=0, description="Number of joins in execution DAG")
    estimated_shuffle_bytes: float = Field(..., ge=0, description="Submission-time estimated shuffle bytes")
    stage_dag_depth: int = Field(..., ge=1, description="Max depth of stage dependency tree")
    stage_dag_branch_factor: int = Field(..., ge=1, description="Max width/branch factor of stage DAG")


class ClusterLoadFeatures(BaseModel):
    queue_depth: int = Field(..., ge=0, description="Active pending Spark applications in queue")
    available_executors: int = Field(..., ge=0, description="Currently idle worker slots")
    available_cores: int = Field(..., ge=0, description="Unallocated CPU cores on cluster")
    colocated_job_count: int = Field(..., ge=0, description="Concurrent running jobs on same cluster")


class AqeCorrection(BaseModel):
    true_post_shuffle_bytes: Optional[float] = Field(
        default=None, ge=0, description="Measured post-shuffle bytes at AQE runtime checkpoint"
    )
    true_partition_count: Optional[int] = Field(
        default=None, ge=0, description="Actual partition count determined by AQE coalesce"
    )


class FeatureVector(BaseModel):
    query_id: str = Field(..., description="Unique query execution identifier")
    stage: Literal["submission", "aqe_checkpoint"] = Field(..., description="Extraction stage")
    plan_features: PlanFeatures
    cluster_load_features: ClusterLoadFeatures
    aqe_correction: AqeCorrection = Field(default_factory=AqeCorrection)


# ----------------- Contract 2: Model Inference Schema -----------------

class ResourceRecommendation(BaseModel):
    num_executors: int = Field(..., ge=1, description="Recommended executor count")
    executor_cores: int = Field(..., ge=1, description="Cores per executor")
    executor_memory_mb: int = Field(..., ge=512, description="RAM per executor in MB")


class PredictionResponse(BaseModel):
    query_id: str
    stage: Literal["submission", "aqe_checkpoint"]
    recommendation: ResourceRecommendation
    confidence: float = Field(..., ge=0.0, le=1.0, description="Variance-derived prediction confidence")
    model_version: str


# ----------------- Contract 3: Calibration Schema -----------------

class ClusterCapacity(BaseModel):
    available_executors: int = Field(..., ge=0)
    available_cores: int = Field(..., ge=0)


class CalibrationInput(BaseModel):
    predicted_num_executors: int = Field(..., ge=1)
    predicted_executor_cores: int = Field(..., ge=1)
    predicted_executor_memory_mb: int = Field(..., ge=512)
    confidence: float = Field(..., ge=0.0, le=1.0)
    cluster_load: ClusterCapacity


class CalibratedRecommendation(BaseModel):
    num_executors: int = Field(..., ge=1)
    executor_cores: int = Field(..., ge=1)
    executor_memory_mb: int = Field(..., ge=512)


class CalibrationOutput(BaseModel):
    calibrated: CalibratedRecommendation
    used_fallback: bool
    reason: Optional[str] = None
