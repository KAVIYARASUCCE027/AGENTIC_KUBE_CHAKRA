"""
Global Event Bus Instance - Phase 18
"""
from services.event_bus import EventBus
from services.publisher_service import PublisherService
from services.subscriber_service import SubscriberService
from services.agent_registry import AgentRegistry
from services.event_correlation_service import EventCorrelationService

# Singleton instances for the entire application
event_bus = EventBus()
publisher = PublisherService(event_bus)
subscriber = SubscriberService(event_bus)
agent_registry = AgentRegistry()
correlation_service = EventCorrelationService(event_bus)
