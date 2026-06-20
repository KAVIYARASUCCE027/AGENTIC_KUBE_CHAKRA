"""
Bootstrap module to initialize agent registry and break circular dependencies.
"""
from services.global_bus import agent_registry
import logging

logger = logging.getLogger(__name__)

def initialize_registry():
    """
    Registers all agents at runtime.
    Called from main.py during startup.
    """
    logger.info("Initializing Agent Registry...")
    from agents.analyzer_agent import AnalyzerAgent
    from agents.root_cause_agent import RootCauseAgent
    from agents.knowledge_agent import KnowledgeAgent
    from agents.recommendation_agent import RecommendationAgent
    from agents.action_planner_agent import ActionPlannerAgent
    from agents.memory_agent import MemoryAgent
    from agents.correlation_agent import CorrelationAgent
    from agents.disk_agent import DiskAgent
    from agents.network_agent import NetworkAgent
    from agents.log_agent import LogAgent
    from agents.k8s_event_agent import K8sEventAgent
    from agents.executor_agent import ExecutorAgent

    agent_registry.register(CorrelationAgent())
    agent_registry.register(AnalyzerAgent())
    agent_registry.register(RootCauseAgent())
    agent_registry.register(KnowledgeAgent())
    agent_registry.register(RecommendationAgent())
    agent_registry.register(ActionPlannerAgent())
    agent_registry.register(MemoryAgent())
    agent_registry.register(DiskAgent())
    agent_registry.register(NetworkAgent())
    agent_registry.register(LogAgent())
    agent_registry.register(K8sEventAgent())
    agent_registry.register(ExecutorAgent())
    
    logger.info("Agent Registry initialized successfully.")
