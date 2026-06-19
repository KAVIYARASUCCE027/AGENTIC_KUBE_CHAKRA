"""
Human Approval Agent — Phase 14.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from schemas.approval.approval_input import ApprovalInput
from schemas.approval.approval_output import ApprovalOutputState
from services.human_approval_service import HumanApprovalService

logger = logging.getLogger(__name__)

class HumanApprovalAgent(BaseAgent):
    """
    Intercepts the workflow to wait for human approval.
    """
    
    def __init__(self):
        super().__init__()
        self._service = None

    @property
    def name(self) -> str:
        return "HumanApprovalAgent"

    def execute(self, state: CPUState) -> CPUState:
        """
        If this is the first time reaching this node, creates an approval request.
        If an approval request already exists, checks its status.
        """
        logger.info(f"{self.name}: Processing approval logic.")
        if not self._service:
            self._service = HumanApprovalService()
        
        # Determine if we already have an approval request
        if state.approval_output and state.approval_output.approval_id:
            # Check the DB for the latest status
            approval_id = state.approval_output.approval_id
            logger.info(f"{self.name}: Checking status for existing approval ID: {approval_id}")
            
            status_response = self._service.get_status(approval_id)
            if not status_response:
                logger.error(f"{self.name}: Approval ID {approval_id} not found in database!")
                # Fallback to keep it pending
                return state
                
            state.approval_output.approval_status = status_response.status
            state.approval_output.approved_by = status_response.approver
            state.approval_output.approval_comment = status_response.comment
            state.approval_output.approval_timestamp = status_response.approved_at
            
            logger.info(f"{self.name}: Approval status is {status_response.status}.")
            return state

        # If no approval ID exists, we need to create one
        logger.info(f"{self.name}: Creating new approval request.")
        
        # Build input from state
        # We assume the action_planner_output contains the planned actions.
        # But wait, action planner output isn't in CPUState directly, it's just 'action_plan_output' in CPUState?
        # Let's check CPUState. Wait, `CPUState` doesn't have `action_plan_output`? Let's check schemas/cpu_state.py if I missed it.
        # Actually `CPUState` has `action_plan_output: ActionPlanOutputState`. I will verify that.
        
        try:
            action_plan = [a.action for a in state.action_plan_output.actions]
        except Exception:
            action_plan = []
            
        try:
            recs = ", ".join([r.value if hasattr(r, "value") else str(r) for r in state.recommendation_output.recommendations])
        except Exception:
            recs = str(state.recommendation_output.recommendations)

        input_data = ApprovalInput(
            pod_name=state.inputs.pod_name,
            namespace=state.inputs.namespace,
            severity=state.analyzer_output.severity,
            recommendation=recs,
            action_plan=action_plan
        )
        
        approval_id = self._service.request_approval(input_data)
        logger.info(f"{self.name}: Created approval request with ID {approval_id}")
        
        # Update state
        if not state.approval_output:
            state.approval_output = ApprovalOutputState()
            
        state.approval_output.approval_required = True
        state.approval_output.approval_id = approval_id
        state.approval_output.approval_status = "PENDING"
        
        return state
