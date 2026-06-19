"""
Knowledge Response Schema — Phase 13.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

from schemas.knowledge.knowledge_chunk import KnowledgeChunk

class KnowledgeResponse(BaseModel):
    """
    Response payload from the standalone Knowledge SRE Agent.
    """
    answer: str = Field(
        ...,
        description="The synthesized answer provided by the Gemini LLM based on the retrieved context."
    )
    sources: List[KnowledgeChunk] = Field(
        default_factory=list,
        description="The top retrieved knowledge chunks that were provided to the LLM."
    )
    confidence_score: float = Field(
        ...,
        description="Average similarity score of the retrieved chunks, representing confidence in the context quality."
    )
    model_name: str = Field(
        ...,
        description="The name of the LLM used to generate the answer."
    )
    execution_time_ms: int = Field(
        ...,
        description="Total time taken to process the request (retrieval + LLM generation)."
    )
    timestamp: datetime = Field(
        ...,
        description="When the response was generated."
    )
