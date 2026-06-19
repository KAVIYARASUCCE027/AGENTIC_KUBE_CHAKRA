"""
Action Planner Input Schema — Phase 8.

Structured input for the Action Planner Agent.
Aggregates metrics, analyzer output, root cause, and recommendations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field

from schemas.recommendation_input import MetricsSnapshot, AnalyzerSummary, RootCauseSummary
from enums.recommendation_type import RecommendationType


class RecommendationSummary(BaseModel):
    """Summary of Phase 7 Recommendations for the Action Planner."""
    recommendations: List[RecommendationType] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)


class ActionPlanInputSchema(BaseModel):
    """
    Validated input contract for the Action Planner Agent.
    Built by action_planner_node from live CPUState.
    """
    pod_name: str
    namespace: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: MetricsSnapshot
    analyzer_output: AnalyzerSummary
    root_cause_output: RootCauseSummary
    recommendation_output: RecommendationSummary
    rag_context: str = Field(default="")
