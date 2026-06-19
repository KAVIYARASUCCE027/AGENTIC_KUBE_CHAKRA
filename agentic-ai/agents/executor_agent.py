"""
Executor Agent — Phase 14.
"""
import logging
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.executor_service import ExecutorService

logger = logging.getLogger(__name__)

class ExecutorAgent(BaseAgent):
    """
    Executes the approved action plan.
    """
    
    def __init__(self):
        super().__init__()
        self._service = ExecutorService(dry_run=True)

    @property
    def name(self) -> str:
        return "ExecutorAgent"

    def execute(self, state: CPUState) -> CPUState:
        """
        Parses the action plan and calls the executor service.
        Updates the execution state.
        """
        logger.info(f"{self.name}: Commencing execution of action plan.")
        
        # Verify approval
        if not state.approval_output or state.approval_output.approval_status != "APPROVED":
            logger.warning(f"{self.name}: Aborting execution. Status is not APPROVED.")
            state.execution_output.execution_status = "SKIPPED"
            state.execution_output.execution_summary = "Skipped because approval was not granted."
            return state
            
        namespace = state.inputs.namespace
        pod_name = state.inputs.pod_name
        
        results: List[Dict[str, Any]] = []
        
        # Parse action plan and execute
        # The action_plan_output has a list of Action objects.
        # We will do some fuzzy matching on the descriptions since this is a simulation.
        
        actions_to_run = []
        if state.action_plan_output and hasattr(state.action_plan_output, "actions"):
            actions_to_run = state.action_plan_output.actions
            
        if not actions_to_run:
            logger.info(f"{self.name}: No actions to execute.")
            state.execution_output.execution_status = "SUCCESS"
            state.execution_output.execution_summary = "No actions were required."
            return state

        for action in actions_to_run:
            desc = action.action.lower()
            if "restart" in desc and "deployment" in desc:
                # Naively extract target, default to pod's base name or something
                target = "app-deployment" 
                res = self._service.restart_deployment(namespace, target)
                results.append(res)
            elif "scale" in desc and "deployment" in desc:
                res = self._service.scale_deployment(namespace, "app-deployment", 3)
                results.append(res)
            elif "delete" in desc and "pod" in desc:
                res = self._service.delete_pod(namespace, pod_name)
                results.append(res)
            elif "cordon" in desc and "node" in desc:
                res = self._service.cordon_node("worker-node-1")
                results.append(res)
            else:
                # Generic fallback simulation
                logger.info(f"[DRY-RUN] Executing generic action: {action.action}")
                results.append({
                    "action": "generic",
                    "target": "unknown",
                    "status": "SUCCESS",
                    "message": f"Simulated generic action: {action.action}"
                })
                
        # Compile summary
        summary_lines = ["Execution Summary (Dry-Run):"]
        for r in results:
            summary_lines.append(f"- [{r['status']}] {r['message']}")
            
        state.execution_output.execution_status = "SUCCESS"
        state.execution_output.execution_summary = "\n".join(summary_lines)
        
        logger.info(f"{self.name}: Execution complete.")
        return state
