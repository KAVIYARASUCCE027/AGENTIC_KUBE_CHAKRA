"""
Publisher Service - Phase 18
"""
import logging
from typing import Dict, Any
from schemas.event_message import EventMessage
from config.event_types import EventType
from config.event_priority import EventPriority
from schemas.common import ResourceSeverity
from services.event_bus import EventBus

import asyncio

logger = logging.getLogger(__name__)

class PublisherService:
    """
    Helper service to format and publish events.
    """
    def __init__(self, event_bus: EventBus):
        self._bus = event_bus

    async def publish_cpu_event(self, source_agent: str, severity: ResourceSeverity, payload: Dict[str, Any]):
        event_type = EventType.CPU_CRITICAL if severity == ResourceSeverity.CRITICAL else EventType.CPU_WARNING
        priority = EventPriority.P2 if severity == ResourceSeverity.CRITICAL else EventPriority.P3
        await self._publish(event_type, source_agent, severity, priority, payload)

    async def publish_memory_event(self, source_agent: str, severity: ResourceSeverity, payload: Dict[str, Any]):
        event_type = EventType.MEMORY_CRITICAL if severity == ResourceSeverity.CRITICAL else EventType.MEMORY_WARNING
        priority = EventPriority.P2 if severity == ResourceSeverity.CRITICAL else EventPriority.P3
        await self._publish(event_type, source_agent, severity, priority, payload)

    async def publish_disk_event(self, source_agent: str, severity: ResourceSeverity, payload: Dict[str, Any]):
        event_type = EventType.DISK_CRITICAL if severity == ResourceSeverity.CRITICAL else EventType.DISK_WARNING
        priority = EventPriority.P2 if severity == ResourceSeverity.CRITICAL else EventPriority.P3
        await self._publish(event_type, source_agent, severity, priority, payload)

    async def publish_network_event(self, source_agent: str, severity: ResourceSeverity, payload: Dict[str, Any]):
        event_type = EventType.NETWORK_CRITICAL if severity == ResourceSeverity.CRITICAL else EventType.NETWORK_WARNING
        priority = EventPriority.P2 if severity == ResourceSeverity.CRITICAL else EventPriority.P3
        await self._publish(event_type, source_agent, severity, priority, payload)

    async def publish_log_event(self, source_agent: str, severity: ResourceSeverity, payload: Dict[str, Any]):
        # Default logic for logs
        event_type = EventType.ERROR_DETECTED
        if payload.get("root_cause", "") == "Application crash":
             event_type = EventType.FATAL_ERROR
        priority = EventPriority.P2 if severity == ResourceSeverity.CRITICAL else EventPriority.P3
        await self._publish(event_type, source_agent, severity, priority, payload)

    async def publish_event_agent_event(self, source_agent: str, severity: ResourceSeverity, payload: Dict[str, Any]):
        root_cause = payload.get("root_cause", "")
        event_type = EventType.CRASH_LOOP_BACKOFF
        if "OOM" in root_cause:
            event_type = EventType.OOM_KILLED
        elif "Scheduling" in root_cause:
            event_type = EventType.FAILED_SCHEDULING
        
        priority = EventPriority.P1 if severity == ResourceSeverity.CRITICAL else EventPriority.P3
        await self._publish(event_type, source_agent, severity, priority, payload)

    async def publish_execution_event(self, source_agent: str, event_type: EventType, payload: Dict[str, Any]):
        await self._publish(event_type, source_agent, ResourceSeverity.LOW, EventPriority.P4, payload)

    async def _publish(self, event_type: EventType, source_agent: str, severity: ResourceSeverity, priority: EventPriority, payload: Dict[str, Any]):
        event = EventMessage(
            event_type=event_type,
            source_agent=source_agent,
            severity=severity,
            priority=priority,
            payload=payload
        )
        await self._bus.publish(event)

    def publish_sync(self, coro):
        """Helper to safely run publish coroutines from synchronous code."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            asyncio.run(coro)
