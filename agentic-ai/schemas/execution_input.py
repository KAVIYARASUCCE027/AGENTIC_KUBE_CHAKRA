"""
Execution Input Schema — Phase 15.
"""
from typing import Optional
from pydantic import BaseModel, Field

class ExecutionInput(BaseModel):
    """
    Input schema for the executor graph.
    """
    incident_id: str = Field(..., description="Unique ID of the incident.")
    cluster_name: str = Field(default="default", description="Target Kubernetes cluster name.")
    namespace: str = Field(default="default", description="Target namespace.")
    deployment_name: str = Field(..., description="Target deployment name.")
    approved_action: str = Field(..., description="The type of action to execute (e.g., SCALE_DEPLOYMENT, ROLLING_RESTART).")
    approval_by: str = Field(default="system", description="Identifier of the approver.")
    replica_count: Optional[int] = Field(default=None, description="Number of replicas (for SCALE_DEPLOYMENT).")
    cpu_limit: Optional[str] = Field(default=None, description="CPU limit/request string (for PATCH_CPU).")
    memory_limit: Optional[str] = Field(default=None, description="Memory limit/request string (for PATCH_MEMORY).")
    rollback_enabled: bool = Field(default=True, description="Whether rollback is enabled if execution fails.")

    class Config:
        json_schema_extra = {
            "title": "ExecutionInput",
            "description": "Defines the payload for executing a Kubernetes action.",
        }
