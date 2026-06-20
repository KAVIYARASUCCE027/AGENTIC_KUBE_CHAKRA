"""
Event Bus - Phase 18
"""
import logging
import asyncio
from typing import Dict, List, Callable, Awaitable
from schemas.event_message import EventMessage
from memory.event_queue import EventQueue
from memory.dead_letter_queue import DeadLetterQueue
from services.retry_service import EventRetryService
import time
from utils.metrics import (
    events_published_total,
    events_processed_total,
    failed_events_total,
    queue_size,
    dead_letter_count,
    event_processing_latency
)

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[EventMessage], Awaitable[None]]

class EventBus:
    """
    Central Asynchronous Event Bus.
    """
    def __init__(self, dlq: DeadLetterQueue = None):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._queue = EventQueue()
        self._dlq = dlq or DeadLetterQueue()
        self._retry_service = EventRetryService(dlq=self._dlq)
        self._processing_task = None
        self._is_running = False

    def subscribe(self, event_type: str, handler: EventHandler):
        """Register a handler for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Handler subscribed to event type: {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Remove a handler."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: EventMessage):
        """Enqueue an event for processing."""
        await self._queue.enqueue(event)
        events_published_total.labels(event_type=event.event_type.value).inc()
        queue_size.set(self._queue.qsize)
        logger.debug(f"Event {event.event_id} of type {event.event_type} published to Event Bus.")

    async def start(self):
        """Start the event processing loop."""
        if self._is_running:
            return
        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_loop())
        logger.info("Event Bus started.")

    async def stop(self):
        """Stop the event processing loop."""
        self._is_running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Event Bus stopped.")

    async def _process_loop(self):
        while self._is_running:
            event = await self._queue.dequeue()
            if event:
                queue_size.set(self._queue.qsize)
                start_time = time.time()
                await self.route_event(event)
                event_processing_latency.labels(event_type=event.event_type.value).observe(time.time() - start_time)
                self._queue.mark_processed(event.event_id)
            else:
                await asyncio.sleep(0.1)

    async def route_event(self, event: EventMessage):
        """Route an event to all its subscribers."""
        handlers = self._subscribers.get(event.event_type, [])
        if not handlers:
            logger.debug(f"No subscribers for event type: {event.event_type}")
            return

        logger.info(f"Routing {event.event_type} to {len(handlers)} subscribers...")
        # Execute handlers concurrently
        tasks = [asyncio.create_task(self._notify_subscriber(handler, event)) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _notify_subscriber(self, handler: EventHandler, event: EventMessage):
        # The retry service handles max retries, backoff, and DLQ pushing
        success = await self._retry_service.execute_with_retry(handler, event)
        agent_name = getattr(handler, '__qualname__', 'unknown_agent')
        if success:
            events_processed_total.labels(event_type=event.event_type.value, agent_name=agent_name).inc()
        else:
            failed_events_total.labels(event_type=event.event_type.value, agent_name=agent_name).inc()
            dead_letter_count.set(self._dlq.count)
