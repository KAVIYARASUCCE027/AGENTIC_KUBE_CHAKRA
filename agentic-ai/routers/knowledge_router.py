"""
Knowledge Router — Phase 13.
"""
import logging
from fastapi import APIRouter, HTTPException

from schemas.knowledge.knowledge_request import KnowledgeRequest
from schemas.knowledge.knowledge_response import KnowledgeResponse
from services.knowledge.knowledge_ingestion_service import KnowledgeIngestionService
from agents.knowledge_sre_agent import KnowledgeSREAgent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"]
)

# Initialize singletons for the router
_ingestion_service = KnowledgeIngestionService()
_sre_agent = KnowledgeSREAgent()

@router.post(
    "/ingest",
    summary="Ingest Local Knowledge",
    description="Reads all markdown files from the local knowledge/ directory, chunks them, and stores them in ChromaDB."
)
async def ingest_knowledge() -> dict:
    try:
        stats = _ingestion_service.ingest_all()
        return {
            "status": "success",
            "message": "Knowledge ingestion completed successfully.",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

@router.post(
    "/ask",
    response_model=KnowledgeResponse,
    summary="Ask the AI SRE Assistant",
    description="Ask a Kubernetes troubleshooting or operational question. Answers are generated using RAG over the internal knowledge base."
)
async def ask_question(request: KnowledgeRequest) -> KnowledgeResponse:
    try:
        response = _sre_agent.ask(request)
        return response
    except Exception as e:
        logger.error(f"Ask question failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {e}")

@router.get(
    "/stats",
    summary="Knowledge Base Statistics",
    description="Returns the total number of chunks stored in each ChromaDB collection."
)
async def get_stats() -> dict:
    try:
        from services.vector_store.chroma_service import ChromaService
        chroma = ChromaService()
        return {
            "status": "success",
            "collections": {
                "incidents": chroma._incidents_col.count(),
                "runbooks": chroma._runbooks_col.count(),
                "kubernetes_docs": chroma._k8s_docs_col.count(),
                "prometheus_guides": chroma._prom_guides_col.count(),
                "knowledge_base": chroma._knowledge_col.count()
            }
        }
    except Exception as e:
        logger.error(f"Stats check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats check failed: {e}")
