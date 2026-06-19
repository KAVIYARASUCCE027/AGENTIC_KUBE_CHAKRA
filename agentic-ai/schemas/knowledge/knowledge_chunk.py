"""
Knowledge Chunk Schema — Phase 13.
"""
from typing import Dict, Any
from pydantic import BaseModel, Field

class KnowledgeChunk(BaseModel):
    """
    Represents a generic chunk of knowledge retrieved from any ChromaDB collection.
    """
    content: str = Field(..., description="The actual text content of the retrieved chunk.")
    source: str = Field(..., description="The origin of this chunk (e.g., file path, runbook name, incident ID).")
    collection: str = Field(..., description="The ChromaDB collection it was retrieved from (e.g., 'runbooks', 'kubernetes_docs').")
    score: float = Field(..., description="The similarity score (0.0 to 1.0) compared to the query.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Any additional metadata attached to the chunk.")
