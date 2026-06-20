"""
Subscriber Service - Phase 18
"""
import logging
from typing import Callable, Awaitable
from schemas.event_message import EventMessage
from services.event_bus import EventBus

logger = logging.getLogger(__name__)

EventHandler = Callable[[EventMessage], Awaitable[None]]

class SubscriberService:
    """
    Helper service to manage subscriptions to the Event Bus.
    """
    def __init__(self, event_bus: EventBus):
        self._bus = event_bus

    def subscribe(self, event_type: str, handler: EventHandler):
        self._bus.subscribe(event_type, handler)

    def unsubscribe(self, event_type: str, handler: EventHandler):
        self._bus.unsubscribe(event_type, handler)
