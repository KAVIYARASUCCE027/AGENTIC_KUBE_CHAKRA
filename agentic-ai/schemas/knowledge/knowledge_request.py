"""
Knowledge Request Schema — Phase 13.
"""
from pydantic import BaseModel, Field

class KnowledgeRequest(BaseModel):
    """
    Request payload for the standalone Knowledge SRE Agent.
    """
    question: str = Field(
        ...,
        description="The operational or troubleshooting question to ask the AI SRE assistant.",
        example="Why is my pod in CrashLoopBackOff?"
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of chunks to retrieve per knowledge collection."
    )
    include_incidents: bool = Field(
        default=True,
        description="Whether to include historical incidents in the search context."
    )
