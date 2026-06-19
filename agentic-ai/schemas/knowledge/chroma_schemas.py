"""
ChromaDB Strongly Typed Schemas — Phase 11.
"""
from pydantic import BaseModel, Field

class ChromaIncident(BaseModel):
    """A similar historical incident retrieved from ChromaDB."""
    incident_id: str
    severity: str
    root_cause: str
    similarity_score: float
    recommendation: str

class ChromaRunbook(BaseModel):
    """A proven historical runbook retrieved from ChromaDB."""
    runbook_id: str
    root_cause_target: str
    similarity_score: float
    action_plan: str

class KnowledgeDocument(BaseModel):
    """An official Kubernetes documentation chunk retrieved from ChromaDB."""
    doc_id: str
    topic: str
    source: str
    similarity_score: float
    content: str
