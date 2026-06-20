"""
Agent Registry — Phase 10, updated Phase 12.
"""
import logging
from typing import Dict, Type, Any


from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class AgentMetrics:
    """Stores health and performance metrics for an agent."""
    def __init__(self):
        self.status = "ACTIVE"
        self.health_score = 100.0
        self.last_seen = datetime.now(timezone.utc)
        self.response_time_ms = 0.0
        self.error_count = 0
        self.events_processed = 0

class AgentRegistry:
    """
    Dynamically loads and registers all agents for the Coordinator, 
    tracking health, metrics, and event subscriptions.
    """
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._metrics: Dict[str, AgentMetrics] = {}
        self._subscriptions: Dict[str, list[str]] = {}

    def register(self, agent: Any):
        """Register a new agent."""
        agent_name = getattr(agent, "name", agent.__class__.__name__)
        if agent_name in self._agents:
            logger.warning(f"Agent '{agent_name}' is already registered. Overwriting.")
        self._agents[agent_name] = agent
        self._metrics[agent_name] = AgentMetrics()
        self._subscriptions[agent_name] = []
        logger.debug(f"Registered agent: {agent_name}")

    def unregister(self, name: str):
        """Remove an agent from the registry."""
        if name in self._agents:
            del self._agents[name]
            del self._metrics[name]
            del self._subscriptions[name]
            logger.debug(f"Unregistered agent: {name}")

    def update_health(self, name: str, response_time_ms: float = None, has_error: bool = False):
        """Update the health metrics of an agent after execution/event handling."""
        if name not in self._metrics:
            return
        
        metrics = self._metrics[name]
        metrics.last_seen = datetime.now(timezone.utc)
        metrics.events_processed += 1
        
        if response_time_ms is not None:
            # Exponential moving average for response time
            metrics.response_time_ms = (metrics.response_time_ms * 0.9) + (response_time_ms * 0.1)

        if has_error:
            metrics.error_count += 1
            metrics.health_score = max(0.0, metrics.health_score - 5.0)
            if metrics.health_score < 50.0:
                metrics.status = "DEGRADED"
        else:
            metrics.health_score = min(100.0, metrics.health_score + 1.0)
            if metrics.health_score >= 50.0:
                metrics.status = "ACTIVE"

    def record_subscription(self, name: str, event_type: str):
        """Record that an agent is subscribed to an event type."""
        if name in self._subscriptions and event_type not in self._subscriptions[name]:
            self._subscriptions[name].append(event_type)

    def get_agent(self, name: str) -> Any:
        """Retrieve an agent by name."""
        if name not in self._agents:
            raise ValueError(f"Agent '{name}' not found in registry.")
        return self._agents[name]

    def get_metrics(self, name: str) -> AgentMetrics:
        """Retrieve metrics for an agent."""
        return self._metrics.get(name)

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
