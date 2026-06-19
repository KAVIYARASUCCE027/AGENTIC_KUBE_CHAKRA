"""
Knowledge Node — Phase 11 (Thin Wrapper).
"""
import logging
import time
from schemas.cpu_state import CPUState
from services.multi_agent_coordinator import MultiAgentCoordinator

logger = logging.getLogger(__name__)

def knowledge_node(state: CPUState) -> CPUState:
    start_time = time.time()
    node_name = "knowledge"
    
    state = state.mark_running(node_name)
    logger.info("[%s] Node started: %s", state.metadata.execution_id, node_name)
    
    coordinator = MultiAgentCoordinator()
    new_state = coordinator.execute_agent(node_name, state)
    
    final_state = new_state.mark_node_completed(node_name)
    
    elapsed = time.time() - start_time
    logger.info("[%s] %s_node completed in %.2fs", final_state.metadata.execution_id, node_name, elapsed)
    
    return final_state
