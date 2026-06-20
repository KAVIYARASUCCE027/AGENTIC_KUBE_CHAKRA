"""
Executor Agent — Phase 15.
"""
import logging
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from schemas.execution_input import ExecutionInput
from schemas.execution_result import ExecutionResult
from graph.executor_graph import executor_graph
from services.global_bus import subscriber, publisher
from config.event_types import EventType
from schemas.event_message import EventMessage

logger = logging.getLogger(__name__)

class ExecutorAgent(BaseAgent):
    """
    Executes the approved action plan using the Executor Graph workflow.
    """
    
    def __init__(self):
        super().__init__()
        # Phase 18
        subscriber.subscribe(EventType.ACTION_APPROVED, self.handle_event)

    async def handle_event(self, event: EventMessage):
        """Async event handler for Event Bus interactions."""
        logger.info(f"ExecutorAgent received event: {event.event_type}")
        if event.event_type == EventType.ACTION_APPROVED:
            # Here it would kick off execution dynamically
            # For backward compatibility, execution is still done in execute(state)
            pass

    @property
    def name(self) -> str:
        return "ExecutorAgent"

    def execute(self, state: CPUState) -> CPUState:
        """
        Parses the action plan and delegates execution to the executor sub-graph.
        """
        logger.info(f"{self.name}: Commencing execution of action plan via sub-graph.")
        
        # Verify approval
        if not state.approval_output or state.approval_output.approval_status != "APPROVED":
            logger.warning(f"{self.name}: Aborting execution. Status is not APPROVED.")
            state.execution_output.execution_status = "SKIPPED"
            state.execution_output.execution_summary = "Skipped because approval was not granted."
            return state
            
        namespace = state.inputs.namespace
        pod_name = state.inputs.pod_name
        incident_id = state.metadata.execution_id
        
        actions_to_run = []
        if state.action_plan_output and hasattr(state.action_plan_output, "actions"):
            actions_to_run = state.action_plan_output.actions
            
        if not actions_to_run:
            logger.info(f"{self.name}: No actions to execute.")
            state.execution_output.execution_status = "SUCCESS"
            state.execution_output.execution_summary = "No actions were required."
            return state

        results: List[ExecutionResult] = []
        
        for action in actions_to_run:
            # Map description/action text to one of the supported actions
            desc = getattr(action, "action", "").upper()
            
            # Simple heuristic to map natural language to the constant actions
            approved_action = "UNKNOWN"
            if "SCALE" in desc:
                approved_action = "SCALE_DEPLOYMENT"
            elif "RESTART" in desc:
                approved_action = "ROLLING_RESTART"
            elif "PATCH CPU" in desc or "LIMITS=CPU" in desc:
                approved_action = "PATCH_CPU"
            elif "PATCH MEMORY" in desc or "LIMITS=MEMORY" in desc:
                approved_action = "PATCH_MEMORY"
            elif "AUTOSCALE" in desc or "HPA" in desc:
                approved_action = "CREATE_HPA"
            else:
                logger.warning(f"Could not map action '{desc}' to a supported operation.")
                continue

            # In a real scenario we'd parse replicas/limits from the LLM output. 
            # We'll use safe defaults if we can't extract them.
            exec_input = ExecutionInput(
                incident_id=incident_id,
                namespace=namespace,
                # Assuming the deployment matches the pod base name. e.g., 'nginx-deployment-7f8f9' -> 'nginx-deployment'
                deployment_name="-".join(pod_name.split("-")[:-2]) if len(pod_name.split("-")) > 2 else pod_name,
                approved_action=approved_action,
                approval_by=state.approval_output.approved_by if state.approval_output else "system",
                replica_count=3,
                cpu_limit="500m",
                memory_limit="512Mi",
                rollback_enabled=True
            )

            # Invoke sub-graph
            logger.info(f"Invoking executor graph for {approved_action}")
            final_sub_state = executor_graph.invoke({"input": exec_input})
            
            if "result" in final_sub_state and final_sub_state["result"]:
                results.append(final_sub_state["result"])

        # Compile summary
        summary_lines = ["Execution Summary (Phase 15):"]
        overall_status = "SUCCESS"
        for r in results:
            summary_lines.append(f"- [{r.status}] {r.action_executed}: {r.message}")
            if r.status not in ["SUCCESS", "ROLLBACK_SUCCESS"]:
                overall_status = "FAILED"
            
        state.execution_output.execution_status = overall_status
        state.execution_output.execution_summary = "\n".join(summary_lines)
        
        logger.info(f"{self.name}: Execution complete with status {overall_status}.")
        return state
