"""
Executor Node — Phase 14.
"""
import logging
from typing import Dict, Any

from agents.executor_agent import ExecutorAgent
from schemas.cpu_state import CPUState

logger = logging.getLogger(__name__)

# Single instance for the lifetime of the graph
_agent = ExecutorAgent()

def executor_node(state: CPUState) -> Dict[str, Any]:
    """
    LangGraph node wrapper for the Executor Agent.
    """
    logger.info("--- NODE: EXECUTOR ---")
    
    updated_state = _agent.execute(state)
    
    return {"execution_output": updated_state.execution_output}
