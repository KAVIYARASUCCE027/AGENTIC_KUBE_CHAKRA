"""
Approval Input Schema — Phase 14.
"""
from typing import List
from pydantic import BaseModel, Field
from schemas.analyzer_output import Severity

class ApprovalInput(BaseModel):
    """
    Data passed into the Human Approval Agent from the graph state.
    """
    pod_name: str
    namespace: str
    severity: str
    recommendation: str
    action_plan: List[str]
