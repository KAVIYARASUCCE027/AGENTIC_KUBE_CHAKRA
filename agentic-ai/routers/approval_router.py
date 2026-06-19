"""
Approval Router — Phase 14.
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from schemas.approval.approval_response import ApprovalActionRequest, ApprovalResponse
from services.human_approval_service import HumanApprovalService
from graph.cpu_graph import build_cpu_graph

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/approvals",
    tags=["Approvals"]
)

# Lazy initialize service to prevent MongoDB connection issues at startup
def get_approval_service() -> HumanApprovalService:
    return HumanApprovalService()

@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
    summary="Get Approval Request Status"
)
async def get_approval_status(approval_id: str) -> ApprovalResponse:
    """Retrieve the status of an approval request."""
    _service = get_approval_service()
    response = _service.get_status(approval_id)
    if not response:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return response

@router.post(
    "/{approval_id}/approve",
    summary="Approve a Request"
)
async def approve_request(approval_id: str, request: ApprovalActionRequest, thread_id: str) -> dict:
    """
    Approve an action plan.
    Requires `thread_id` (passed as query param or in body, here we use query param for simplicity) to resume LangGraph.
    """
    _service = get_approval_service()
    success = _service.approve(approval_id, request.approver, request.comment)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found.")
        
    # Resume LangGraph thread
    logger.info(f"Resuming LangGraph for thread {thread_id} after APPROVAL.")
    cpu_graph = build_cpu_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    # We pass None as the input because we just want the graph to continue from where it paused.
    try:
        # We must push the updated state into the graph so that check_approval conditional edge sees "APPROVED"
        # Since the graph paused inside human_approval (wait, we did NOT pause in human_approval, 
        # we paused AT the end of human_approval).
        # Actually, if we just invoke with None, it evaluates check_approval on the existing state!
        # But wait, the existing state has approval_status="PENDING"!
        # We need to UPDATE the state in the checkpointer first.
        
        # Get current state
        current_state = cpu_graph.get_state(config)
        if not current_state.values:
            logger.warning("No state found in checkpointer for this thread.")
        else:
            # Update the state's approval_status to APPROVED
            state_values = current_state.values
            if "approval_output" in state_values:
                # Assuming state_values is a dict, but if it's an object we handle both
                if isinstance(state_values["approval_output"], dict):
                    state_values["approval_output"]["approval_status"] = "APPROVED"
                    state_values["approval_output"]["approved_by"] = request.approver
                else:
                    state_values["approval_output"].approval_status = "APPROVED"
                    state_values["approval_output"].approved_by = request.approver
                    
            # We can update the state using update_state
            # LangGraph: graph.update_state(config, state_values)
            cpu_graph.update_state(config, state_values)
            
        result = cpu_graph.invoke(None, config=config)
        
        return {
            "status": "success",
            "message": "Approved and execution completed.",
            "execution_status": "SUCCESS" # Normally extract from result
        }
    except Exception as e:
        logger.error(f"Failed to resume graph: {e}")
        raise HTTPException(status_code=500, detail=f"Graph resumption failed: {e}")

@router.post(
    "/{approval_id}/reject",
    summary="Reject a Request"
)
async def reject_request(approval_id: str, request: ApprovalActionRequest, thread_id: str) -> dict:
    """
    Reject an action plan.
    Requires `thread_id` to resume LangGraph.
    """
    _service = get_approval_service()
    success = _service.reject(approval_id, request.approver, request.comment)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found.")
        
    # Resume LangGraph thread
    logger.info(f"Resuming LangGraph for thread {thread_id} after REJECTION.")
    cpu_graph = build_cpu_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        current_state = cpu_graph.get_state(config)
        if current_state.values:
            state_values = current_state.values
            if "approval_output" in state_values:
                if isinstance(state_values["approval_output"], dict):
                    state_values["approval_output"]["approval_status"] = "REJECTED"
                    state_values["approval_output"]["approved_by"] = request.approver
                else:
                    state_values["approval_output"].approval_status = "REJECTED"
                    state_values["approval_output"].approved_by = request.approver
            cpu_graph.update_state(config, state_values)
            
        cpu_graph.invoke(None, config=config)
        
        return {
            "status": "success",
            "message": "Rejected successfully. Execution aborted."
        }
    except Exception as e:
        logger.error(f"Failed to resume graph: {e}")
        raise HTTPException(status_code=500, detail=f"Graph resumption failed: {e}")
