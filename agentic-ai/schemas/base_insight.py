"""
Base Insight Schema — Phase 16.
"""
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field

from schemas.common import ResourceSeverity

class ResourceTrend(str, Enum):
    INCREASING = "INCREASING"
    STABLE = "STABLE"
    DECREASING = "DECREASING"
    UNKNOWN = "UNKNOWN"

class BaseInsightInputs(BaseModel):
    pod_name: str = Field(default="")
    namespace: str = Field(default="default")
    node_name: str = Field(default="")
    cluster_name: str = Field(default="default")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BaseInsightMetrics(BaseModel):
    usage: str = Field(default="")
    request: str = Field(default="")
    limit: str = Field(default="")
    trend: ResourceTrend = Field(default=ResourceTrend.UNKNOWN)
    
class BaseInsightOutputs(BaseModel):
    severity: ResourceSeverity = Field(default=ResourceSeverity.LOW)
    analysis: str = Field(default="")
    root_cause: str = Field(default="")
    recommendations: List[str] = Field(default_factory=list)

class BaseInsight(BaseModel):
    inputs: BaseInsightInputs = Field(default_factory=BaseInsightInputs)
    metrics: BaseInsightMetrics = Field(default_factory=BaseInsightMetrics)
    outputs: BaseInsightOutputs = Field(default_factory=BaseInsightOutputs)
