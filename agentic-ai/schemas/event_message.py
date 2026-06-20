"""
Event Message Schema - Phase 18
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field

from config.event_types import EventType
from config.event_priority import EventPriority
from schemas.common import ResourceSeverity

class EventMessage(BaseModel):
    """
    Standard schema for all events sent over the Event Bus.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    source_agent: str
    target_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: ResourceSeverity = Field(default=ResourceSeverity.LOW)
    priority: EventPriority = Field(default=EventPriority.P3)
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
