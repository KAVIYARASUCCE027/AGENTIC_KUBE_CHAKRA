"""
Event Insight Schema — Phase 16.
"""
from schemas.base_insight import BaseInsight, BaseInsightMetrics
from pydantic import Field
from typing import List

class EventMetrics(BaseInsightMetrics):
    failed_scheduling_count: int = Field(default=0)
    oom_killed_count: int = Field(default=0)
    backoff_count: int = Field(default=0)
    critical_events: List[str] = Field(default_factory=list)

class EventInsight(BaseInsight):
    metrics: EventMetrics = Field(default_factory=EventMetrics)
