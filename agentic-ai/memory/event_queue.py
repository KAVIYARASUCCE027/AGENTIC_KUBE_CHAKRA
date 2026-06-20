"""
Event Queue - Phase 18
"""
import logging
import asyncio
from typing import List, Optional
from schemas.event_message import EventMessage

logger = logging.getLogger(__name__)

class EventQueue:
    """
    In-memory async event queue supporting deduplication and prioritization.
    """
    def __init__(self):
        self._queue = asyncio.PriorityQueue()
        self._processed_events = set()
        self._pending_events = set()

    async def enqueue(self, event: EventMessage):
        """Add an event to the queue."""
        if event.event_id in self._processed_events or event.event_id in self._pending_events:
            logger.debug(f"Event {event.event_id} already exists or processed. Skipping.")
            return

        self._pending_events.add(event.event_id)
        # PriorityQueue uses the first element of a tuple for ordering.
        await self._queue.put((event.priority.value, event))
        logger.debug(f"Enqueued event {event.event_type} (Priority: P{event.priority.value})")

    async def dequeue(self) -> Optional[EventMessage]:
        """Remove and return an event from the queue."""
        if self._queue.empty():
            return None
        
        _, event = await self._queue.get()
        self._pending_events.remove(event.event_id)
        return event

    def mark_processed(self, event_id: str):
        """Mark an event as fully processed."""
        self._processed_events.add(event_id)

    @property
    def qsize(self) -> int:
        return self._queue.qsize()

    @property
    def processed_count(self) -> int:
        return len(self._processed_events)
