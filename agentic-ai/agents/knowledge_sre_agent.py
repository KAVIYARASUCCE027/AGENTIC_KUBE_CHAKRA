"""
Knowledge SRE Agent — Phase 13.

Standalone agent for answering natural-language SRE questions
using retrieved knowledge. Does NOT implement BaseAgent
or integrate into the LangGraph CPU pipeline.
"""
import time
import logging

from schemas.knowledge.knowledge_request import KnowledgeRequest
from schemas.knowledge.knowledge_response import KnowledgeResponse
from services.knowledge.knowledge_retriever_service import KnowledgeRetrieverService
from services.gemini.gemini_knowledge_service import GeminiKnowledgeService

logger = logging.getLogger(__name__)

class KnowledgeSREAgent:
    """
    Acts as an AI-powered Kubernetes SRE assistant.
    Flow: Question -> Retriever -> Gemini -> Structured Answer
    """
    
    def __init__(self):
        self._retriever = KnowledgeRetrieverService()
        self._gemini = GeminiKnowledgeService()
        logger.info("KnowledgeSREAgent initialized.")

    def ask(self, request: KnowledgeRequest) -> KnowledgeResponse:
        """
        Processes a knowledge request from start to finish.
        """
        start_t = time.perf_counter()
        logger.info(f"KnowledgeSREAgent answering: '{request.question}'")
        
        # 1. Retrieve knowledge chunks
        chunks = self._retriever.retrieve(
            question=request.question,
            top_k=request.top_k,
            include_incidents=request.include_incidents
        )
        
        if not chunks:
            logger.warning("KnowledgeSREAgent: No relevant chunks found. Proceeding with empty context.")
            
        # 2. Answer question using LLM
        response = self._gemini.answer_question(
            question=request.question,
            chunks=chunks
        )
        
        elapsed_ms = int((time.perf_counter() - start_t) * 1000)
        logger.info(f"KnowledgeSREAgent finished in {elapsed_ms}ms with confidence {response.confidence_score}.")
        
        # Ensure total execution time is captured accurately
        response.execution_time_ms = elapsed_ms
        return response
