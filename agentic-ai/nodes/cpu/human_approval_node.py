"""
Human Approval Node — Phase 14.
"""
import logging
from typing import Dict, Any

from agents.human_approval_agent import HumanApprovalAgent
from schemas.cpu_state import CPUState

logger = logging.getLogger(__name__)

# Single instance for the lifetime of the graph
_agent = HumanApprovalAgent()

def human_approval_node(state: CPUState) -> Dict[str, Any]:
    """
    LangGraph node wrapper for the Human Approval Agent.
    """
    logger.info("--- NODE: HUMAN APPROVAL ---")
    
    updated_state = _agent.execute(state)
    
    # LangGraph expects a dict mapping for the keys to update
    return {"approval_output": updated_state.approval_output}
