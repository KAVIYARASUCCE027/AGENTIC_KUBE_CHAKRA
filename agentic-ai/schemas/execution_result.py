"""
Execution Result Schema — Phase 15.
"""
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ExecutionResult(BaseModel):
    """
    Output schema for the executor graph and individual operations.
    """
    status: str = Field(default="PENDING", description="Execution status (SUCCESS, FAILED, PENDING, ROLLBACK_SUCCESS, ROLLBACK_FAILED).")
    action_executed: str = Field(..., description="The action that was executed.")
    command: str = Field(default="", description="The specific kubectl command run.")
    message: str = Field(default="", description="Detailed message or output from the command.")
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Execution start timestamp.")
    end_time: Optional[datetime] = Field(default=None, description="Execution end timestamp.")
    rollback_available: bool = Field(default=False, description="Whether a rollback is available/was backed up.")

    class Config:
        json_schema_extra = {
            "title": "ExecutionResult",
            "description": "Defines the output result of a Kubernetes action execution.",
        }
