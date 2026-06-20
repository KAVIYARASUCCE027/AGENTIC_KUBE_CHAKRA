"""
Verification Node — Phase 15.
"""
import logging
from datetime import datetime, timezone

from schemas.execution_graph_state import ExecutionGraphState
from services.kubernetes_service import KubernetesService
from services.rollback_service import RollbackService

logger = logging.getLogger(__name__)

def verification_node(state: ExecutionGraphState) -> ExecutionGraphState:
    """
    Verifies execution success. If it fails, trigger rollback.
    """
    logger.info("--- NODE: VERIFICATION ---")
    
    res = state.get("result")
    if not res:
        logger.error("No execution result found in state.")
        return state

    if res.status != "SUCCESS":
        logger.warning(f"Skipping verification because execution status is {res.status}")
        return state

    k8s = KubernetesService()
    inp = state["input"]

    logger.info(f"Verifying deployment {inp.deployment_name}...")
    success, msg = k8s.verify_execution(inp.namespace, inp.deployment_name)
    
    if success:
        logger.info("Verification succeeded.")
        res.message += f"\n[Verification] SUCCESS: {msg}"
    else:
        logger.error(f"Verification failed: {msg}")
        res.status = "VERIFICATION_FAILED"
        res.message += f"\n[Verification] FAILED: {msg}"
        
        # Trigger Rollback
        if inp.rollback_enabled:
            logger.info("Initiating automatic rollback...")
            rollback_svc = RollbackService(k8s)
            action = res.action_executed
            
            rb_res = {}
            if action in ["SCALE_DEPLOYMENT", "PATCH_CPU", "PATCH_MEMORY"]:
                rb_res = rollback_svc._apply_yaml_backup(inp.namespace, state.get("backup_yaml", ""))
            elif action == "ROLLING_RESTART":
                rb_res = rollback_svc.rollback_restart(inp.namespace, inp.deployment_name)
            else:
                rb_res = {"status": "FAILED", "message": "Rollback not supported for this action."}
                
            if rb_res.get("status") == "SUCCESS":
                res.status = "ROLLBACK_SUCCESS"
                res.message += f"\n[Rollback] SUCCESS: {rb_res.get('message')}"
            else:
                res.status = "ROLLBACK_FAILED"
                res.message += f"\n[Rollback] FAILED: {rb_res.get('message')}"
                
    res.end_time = datetime.now(timezone.utc)
    state["result"] = res
    return state
