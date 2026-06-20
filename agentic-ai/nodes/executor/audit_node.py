"""
Audit Node — Phase 15.
"""
import logging
from schemas.execution_graph_state import ExecutionGraphState
from services.audit_service import AuditService

logger = logging.getLogger(__name__)

def audit_node(state: ExecutionGraphState) -> ExecutionGraphState:
    """
    Saves the execution result to the ChromaDB audit log.
    """
    logger.info("--- NODE: AUDIT ---")
    
    res = state.get("result")
    inp = state.get("input")
    
    if not res or not inp:
        logger.error("Missing result or input for audit node.")
        return state

    audit_svc = AuditService()
    
    audit_id = audit_svc.log_execution(
        incident_id=inp.incident_id,
        action_type=res.action_executed,
        command=res.command,
        status=res.status,
        executed_by=inp.approval_by,
        rollback_reference="yes" if res.rollback_available else "no"
    )
    
    state["audit_id"] = audit_id
    return state
