"""
Memory Node — Phase 15.
"""
import logging
from schemas.execution_graph_state import ExecutionGraphState
from memory.execution_history import ExecutionHistoryMemory

logger = logging.getLogger(__name__)

def memory_node(state: ExecutionGraphState) -> ExecutionGraphState:
    """
    Saves the execution history into ChromaDB.
    """
    logger.info("--- NODE: MEMORY ---")
    
    res = state.get("result")
    inp = state.get("input")
    
    if not res or not inp:
        logger.error("Missing result or input for memory node.")
        return state

    history_mem = ExecutionHistoryMemory()
    
    history_id = history_mem.add_history(
        incident_id=inp.incident_id,
        action=res.action_executed,
        result=res.status,
        rollback_reference="yes" if res.rollback_available else "no"
    )
    
    state["history_id"] = history_id
    return state
