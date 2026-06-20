"""
Disk Insight Schema — Phase 16.
"""
from schemas.base_insight import BaseInsight, BaseInsightMetrics
from pydantic import Field

class DiskMetrics(BaseInsightMetrics):
    ephemeral_storage_usage: str = Field(default="")
    disk_io_read: str = Field(default="")
    disk_io_write: str = Field(default="")

class DiskInsight(BaseInsight):
    metrics: DiskMetrics = Field(default_factory=DiskMetrics)
