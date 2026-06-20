"""
Executor Node — Phase 15.
"""
import logging
from datetime import datetime, timezone

from schemas.execution_graph_state import ExecutionGraphState
from schemas.execution_result import ExecutionResult
from services.kubernetes_service import KubernetesService

logger = logging.getLogger(__name__)

def executor_node(state: ExecutionGraphState) -> ExecutionGraphState:
    """
    Executes the Kubernetes action and creates a backup.
    """
    logger.info("--- NODE: EXECUTOR ---")
    k8s = KubernetesService()
    inp = state["input"]

    # 1. Backup deployment configuration if rollback is enabled
    backup_yaml = None
    if inp.rollback_enabled:
        logger.info(f"Creating backup for {inp.deployment_name} in {inp.namespace}...")
        backup_yaml = k8s.backup_deployment(inp.namespace, inp.deployment_name)
        if not backup_yaml:
            logger.warning("Backup failed. Proceeding without backup.")

    # 2. Execute action
    action = inp.approved_action
    logger.info(f"Executing action: {action}")
    
    start_time = datetime.now(timezone.utc)
    res_dict = {}

    if action == "SCALE_DEPLOYMENT":
        replicas = inp.replica_count if inp.replica_count is not None else 1
        res_dict = k8s.scale_deployment(inp.namespace, inp.deployment_name, replicas)
    elif action == "ROLLING_RESTART":
        res_dict = k8s.rollout_restart(inp.namespace, inp.deployment_name)
    elif action == "PATCH_CPU":
        limit = inp.cpu_limit if inp.cpu_limit else "500m"
        res_dict = k8s.patch_cpu(inp.namespace, inp.deployment_name, limit)
    elif action == "PATCH_MEMORY":
        limit = inp.memory_limit if inp.memory_limit else "512Mi"
        res_dict = k8s.patch_memory(inp.namespace, inp.deployment_name, limit)
    elif action == "CREATE_HPA":
        res_dict = k8s.create_hpa(inp.namespace, inp.deployment_name)
    else:
        res_dict = {"status": "FAILED", "message": f"Unsupported action: {action}", "command": ""}

    end_time = datetime.now(timezone.utc)

    # 3. Save result
    state["backup_yaml"] = backup_yaml
    state["result"] = ExecutionResult(
        status=res_dict.get("status", "FAILED"),
        action_executed=action,
        command=res_dict.get("command", ""),
        message=res_dict.get("message", ""),
        start_time=start_time,
        end_time=end_time,
        rollback_available=bool(backup_yaml)
    )

    return state
