"""
Agent Registry — Phase 10, updated Phase 12.
"""
import logging
from typing import Dict, Type
from agents.base_agent import BaseAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.root_cause_agent import RootCauseAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.recommendation_agent import RecommendationAgent
from agents.action_planner_agent import ActionPlannerAgent
from agents.memory_agent import MemoryAgent
from agents.correlation_agent import CorrelationAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Dynamically loads and registers all agents for the Coordinator.
    """
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(CorrelationAgent())
        self.register(AnalyzerAgent())
        self.register(RootCauseAgent())
        self.register(KnowledgeAgent())
        self.register(RecommendationAgent())
        self.register(ActionPlannerAgent())
        self.register(MemoryAgent())

    def register(self, agent: BaseAgent):
        """Register a new agent."""
        if agent.name in self._agents:
            logger.warning(f"Agent '{agent.name}' is already registered. Overwriting.")
        self._agents[agent.name] = agent
        logger.debug(f"Registered agent: {agent.name}")

    def get_agent(self, name: str) -> BaseAgent:
        """Retrieve an agent by name."""
        if name not in self._agents:
            raise ValueError(f"Agent '{name}' not found in registry.")
        return self._agents[name]

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
