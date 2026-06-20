"""
Multi-Resource State Schema — Phase 16.
"""
from pydantic import BaseModel, Field
from typing import Optional

from schemas.cpu_state import CPUState
from schemas.memory_insight import MemoryInsight
from schemas.disk_insight import DiskInsight
from schemas.network_insight import NetworkInsight
from schemas.log_insight import LogInsight
from schemas.event_insight import EventInsight

class MultiResourceState(BaseModel):
    """
    Shared state for the multi-resource observability LangGraph workflow.
    """
    cpu_state: CPUState
    memory_insight: Optional[MemoryInsight] = Field(default=None)
    disk_insight: Optional[DiskInsight] = Field(default=None)
    network_insight: Optional[NetworkInsight] = Field(default=None)
    log_insight: Optional[LogInsight] = Field(default=None)
    event_insight: Optional[EventInsight] = Field(default=None)

