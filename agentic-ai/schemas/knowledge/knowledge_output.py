"""
Knowledge Output Schema — Phase 11.
"""
from typing import List
from pydantic import BaseModel, Field

class KnowledgeAgentOutput(BaseModel):
    """
    RAG Context built by the Knowledge Agent.
    Injected into CPUState for downstream agents.
    """
    rag_context: str = Field(default="")
    confidence: float = Field(default=0.0)
    source_count: int = Field(default=0)
    retrieved_incident_ids: List[str] = Field(default_factory=list)
    retrieved_runbook_ids: List[str] = Field(default_factory=list)
    retrieved_document_ids: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "title": "KnowledgeAgentOutput",
            "description": "RAG context and metadata output by the Knowledge Agent.",
        }
