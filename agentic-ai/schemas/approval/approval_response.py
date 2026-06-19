"""
Approval API Request/Response Schemas — Phase 14.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ApprovalActionRequest(BaseModel):
    """
    Payload required to approve or reject a request.
    """
    approver: str
    comment: Optional[str] = None

class ApprovalResponse(BaseModel):
    """
    API Response for a single approval request.
    """
    id: str
    pod_name: str
    namespace: str
    severity: str
    recommendation: str
    action_plan: List[str]
    status: str
    approver: Optional[str]
    comment: Optional[str]
    created_at: datetime
    approved_at: Optional[datetime]
