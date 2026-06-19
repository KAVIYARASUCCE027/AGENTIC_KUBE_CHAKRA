"""
Execution Output State Schema — Phase 14.
"""
from typing import Optional
from pydantic import BaseModel, Field

class ExecutionOutputState(BaseModel):
    """
    Execution state representing the result of the Executor agent.
    """
    execution_status: str = Field(default="NOT_STARTED", description="Status: NOT_STARTED, SUCCESS, FAILED, SKIPPED")
    execution_summary: Optional[str] = Field(default=None, description="Detailed summary of the execution results.")
