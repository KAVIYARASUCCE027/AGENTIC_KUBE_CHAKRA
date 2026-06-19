"""
Approval Output Schema — Phase 14.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ApprovalOutputState(BaseModel):
    """
    Execution state representation of human approval.
    """
    approval_required: bool = Field(default=True, description="Whether human approval is required to execute actions.")
    approval_id: Optional[str] = Field(default=None, description="The UUID of the approval request in the database.")
    approval_status: str = Field(default="PENDING", description="Status: PENDING, APPROVED, REJECTED")
    approved_by: Optional[str] = Field(default=None, description="The user who approved or rejected the request.")
    approval_comment: Optional[str] = Field(default=None, description="Comments provided by the approver.")
    approval_timestamp: Optional[datetime] = Field(default=None, description="When the approval action occurred.")
