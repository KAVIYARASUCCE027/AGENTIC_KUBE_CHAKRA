"""
Human Approval Service — Phase 14.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from models.approval_request import ApprovalRequestModel
from repositories.approval_repository import ApprovalRepository
from schemas.approval.approval_input import ApprovalInput
from schemas.approval.approval_response import ApprovalResponse

class HumanApprovalService:
    """
    Business logic for managing human approval requests.
    """
    def __init__(self):
        self._repo = ApprovalRepository()

    def request_approval(self, input_data: ApprovalInput) -> str:
        """
        Creates a new approval request in the database and returns its UUID.
        """
        approval_id = str(uuid.uuid4())
        
        request_model = ApprovalRequestModel(
            id=approval_id,
            pod_name=input_data.pod_name,
            namespace=input_data.namespace,
            severity=input_data.severity,
            recommendation=input_data.recommendation,
            action_plan=input_data.action_plan,
            status="PENDING"
        )
        
        return self._repo.save_request(request_model)

    def approve(self, approval_id: str, approver: str, comment: Optional[str] = None) -> bool:
        """
        Marks an approval request as APPROVED.
        """
        approved_at = datetime.now(timezone.utc)
        return self._repo.update_status(
            approval_id=approval_id,
            status="APPROVED",
            approver=approver,
            comment=comment,
            approved_at=approved_at
        )

    def reject(self, approval_id: str, approver: str, comment: Optional[str] = None) -> bool:
        """
        Marks an approval request as REJECTED.
        """
        approved_at = datetime.now(timezone.utc)
        return self._repo.update_status(
            approval_id=approval_id,
            status="REJECTED",
            approver=approver,
            comment=comment,
            approved_at=approved_at
        )

    def get_status(self, approval_id: str) -> Optional[ApprovalResponse]:
        """
        Retrieves the status of an approval request.
        """
        model = self._repo.find_by_id(approval_id)
        if not model:
            return None
            
        return ApprovalResponse(
            id=model.id,
            pod_name=model.pod_name,
            namespace=model.namespace,
            severity=model.severity,
            recommendation=model.recommendation,
            action_plan=model.action_plan,
            status=model.status,
            approver=model.approver,
            comment=model.comment,
            created_at=model.created_at,
            approved_at=model.approved_at
        )
