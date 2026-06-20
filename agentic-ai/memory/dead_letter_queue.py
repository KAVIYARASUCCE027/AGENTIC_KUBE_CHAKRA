"""
Dead Letter Queue - Phase 18
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from schemas.event_message import EventMessage

logger = logging.getLogger(__name__)

class DeadLetterQueue:
    """
    In-memory queue for persistently failed events.
    """
    def __init__(self):
        self._failed_events: List[Dict[str, Any]] = []

    def add(self, event: EventMessage, reason: str):
        """Store an unrecoverable event."""
        record = {
            "event": event,
            "reason": reason,
            "failed_at": datetime.now(timezone.utc).isoformat()
        }
        self._failed_events.append(record)
        logger.warning(f"Event {event.event_id} sent to DLQ. Reason: {reason}")

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all failed events for inspection."""
        return self._failed_events

    def clear(self):
        """Clear the dead letter queue."""
        self._failed_events.clear()

    @property
    def count(self) -> int:
        return len(self._failed_events)
