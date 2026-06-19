"""
Approval Request Database Model — Phase 14.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ApprovalRequestModel(BaseModel):
    """
    Database representation of an approval request.
    """
    id: str = Field(..., description="Unique UUID for the approval request.")
    pod_name: str
    namespace: str
    severity: str
    recommendation: str
    action_plan: List[str]
    status: str = Field(default="PENDING", description="Status: PENDING, APPROVED, REJECTED")
    approver: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    approved_at: Optional[datetime] = None
