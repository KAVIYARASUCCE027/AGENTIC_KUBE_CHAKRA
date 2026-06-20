"""
Event Correlation Service - Phase 18
"""
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

from schemas.event_message import EventMessage
from config.event_types import EventType
from config.event_priority import EventPriority
from schemas.common import ResourceSeverity
from services.event_bus import EventBus
from services.publisher_service import PublisherService
from services.subscriber_service import SubscriberService

logger = logging.getLogger(__name__)

class EventCorrelationService:
    """
    Analyzes incoming events over a time window to identify correlated incidents.
    """
    def __init__(self, event_bus: EventBus):
        self._bus = event_bus
        self._publisher = PublisherService(event_bus)
        self._subscriber = SubscriberService(event_bus)
        self._recent_events: List[EventMessage] = []
        self._correlation_window = timedelta(minutes=5)
        self._subscribe_to_criticals()

    def _subscribe_to_criticals(self):
        """Subscribe to all potential root-cause precursor events."""
        events_to_monitor = [
            EventType.CPU_CRITICAL, EventType.MEMORY_CRITICAL,
            EventType.DISK_CRITICAL, EventType.NETWORK_CRITICAL,
            EventType.TIMEOUT_EXCEPTION, EventType.FATAL_ERROR,
            EventType.OOM_KILLED, EventType.CRASH_LOOP_BACKOFF,
            EventType.FAILED_SCHEDULING
        ]
        for ev in events_to_monitor:
            self._subscriber.subscribe(ev, self.handle_event)

    async def handle_event(self, event: EventMessage):
        """Buffer incoming events and run correlation."""
        self._recent_events.append(event)
        self._clean_old_events()
        await self._correlate()

    def _clean_old_events(self):
        """Remove events outside the correlation window."""
        now = datetime.now(timezone.utc)
        self._recent_events = [
            ev for ev in self._recent_events 
            if now - ev.timestamp <= self._correlation_window
        ]

    async def _correlate(self):
        """Run correlation rules."""
        event_types = {ev.event_type for ev in self._recent_events}
        
        # Rule 1: Application Overload
        if EventType.CPU_CRITICAL in event_types and (EventType.TIMEOUT_EXCEPTION in event_types or EventType.CRASH_LOOP_BACKOFF in event_types):
            await self._trigger_correlated(EventType.APPLICATION_OVERLOAD, "High CPU combined with timeouts or crashes indicates overload.")

        # Rule 2: Resource Exhaustion
        if EventType.MEMORY_CRITICAL in event_types and EventType.OOM_KILLED in event_types:
            await self._trigger_correlated(EventType.RESOURCE_EXHAUSTION, "Memory Critical and OOMKilled detected.")

        # Rule 3: Node Failure
        if EventType.NETWORK_CRITICAL in event_types and EventType.FAILED_SCHEDULING in event_types:
            await self._trigger_correlated(EventType.NODE_FAILURE, "Network Critical and Scheduling Failure implies node networking issues.")

    async def _trigger_correlated(self, event_type: EventType, reason: str):
        """Publish a correlated event."""
        # Prevent spamming the same correlated event in a short window
        correlated_already = any(ev.event_type == event_type for ev in self._recent_events)
        if correlated_already:
            return

        logger.info(f"Correlation identified: {event_type} - {reason}")
        
        # Publish the new correlated event
        event = EventMessage(
            event_type=event_type,
            source_agent="EventCorrelationService",
            target_agent="SupervisorAgent",
            severity=ResourceSeverity.CRITICAL,
            priority=EventPriority.P1,
            payload={"reason": reason, "correlated_events": [ev.event_id for ev in self._recent_events]}
        )
        await self._bus.publish(event)
        # Add it to local buffer so we don't trigger it repeatedly
        self._recent_events.append(event)
