"""
Memory Insight Schema — Phase 16.
"""
from schemas.base_insight import BaseInsight, BaseInsightMetrics, ResourceTrend
from pydantic import Field

class MemoryMetrics(BaseInsightMetrics):
    oom_killed_count: int = Field(default=0)
    restart_count: int = Field(default=0)

class MemoryInsight(BaseInsight):
    metrics: MemoryMetrics = Field(default_factory=MemoryMetrics)
