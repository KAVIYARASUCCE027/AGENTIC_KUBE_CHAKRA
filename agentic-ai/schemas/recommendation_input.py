"""
Recommendation Input Schema — Phase 7.

Structured input for the Recommendation Agent.
Aggregates metrics, analyzer output, and root cause output into a
single validated contract.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field

from schemas.analyzer_output import HealthStatus, Severity, AbnormalityType
from enums.root_cause_type import RootCauseType


class MetricsSnapshot(BaseModel):
    """Compact metric snapshot passed to the Recommendation Agent."""
    cpu_usage: float = Field(description="Current CPU usage %.")
    avg_cpu_5m: float = Field(default=0.0, description="5m average CPU %.")
    avg_cpu_15m: float = Field(default=0.0, description="15m average CPU %.")
    cpu_trend: str = Field(default="STABLE", description="INCREASING, STABLE, DECREASING.")
    cpu_limit: float = Field(default=0.0)
    cpu_request: float = Field(default=0.0)
    restart_count: int = Field(default=0)
    replica_count: int = Field(default=0)
    throttling_percentage: float = Field(default=0.0)


class AnalyzerSummary(BaseModel):
    """Summary of Phase 5 Analyzer output for the Recommendation Agent."""
    health_status: HealthStatus
    severity: Severity
    abnormality: AbnormalityType
    trend: str = Field(default="STABLE")
    confidence: int = Field(default=0, ge=0, le=100)
    reasoning: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class RootCauseSummary(BaseModel):
    """Summary of Phase 6 Root Cause output for the Recommendation Agent."""
    root_cause: RootCauseType
    confidence: int = Field(default=0, ge=0, le=100)
    evidence: List[str] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    source: str = Field(default="FALLBACK")


class RecommendationInputSchema(BaseModel):
    """
    Validated input contract for the Recommendation Agent.
    Built by recommendation_node from live CPUState.
    """
    pod_name: str
    namespace: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: MetricsSnapshot
    analyzer_output: AnalyzerSummary
    root_cause_output: RootCauseSummary
    rag_context: str = Field(default="")
