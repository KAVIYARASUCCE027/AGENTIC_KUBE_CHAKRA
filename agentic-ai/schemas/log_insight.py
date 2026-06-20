"""
Log Insight Schema — Phase 16.
"""
from schemas.base_insight import BaseInsight, BaseInsightMetrics
from pydantic import Field

class LogMetrics(BaseInsightMetrics):
    error_count: int = Field(default=0)
    warn_count: int = Field(default=0)
    fatal_count: int = Field(default=0)
    crashloop_detected: bool = Field(default=False)

class LogInsight(BaseInsight):
    metrics: LogMetrics = Field(default_factory=LogMetrics)
