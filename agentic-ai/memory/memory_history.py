"""
Memory History — Phase 16.
"""
import uuid
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from services.vector_store.chroma_service import ChromaService
from services.embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class MemoryHistory:
    """
    Stores memory incidents in ChromaDB.
    """
    def __init__(self):
        self._chroma = ChromaService()
        self._embedding = EmbeddingService()

    def add_history(self, pod_name: str, severity: str, root_cause: str, recommendations: str) -> str:
        history_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        document = f"Memory Incident for {pod_name}: Severity {severity}, Root Cause '{root_cause}', Recommendations: {recommendations}."
        metadata = {
            "pod_name": pod_name,
            "severity": severity,
            "root_cause": root_cause,
            "timestamp": timestamp
        }
        
        try:
            vector = self._embedding.generate_embedding(document)
            if vector:
                self._chroma.add_memory_history(history_id, document, metadata, vector)
                logger.info(f"Memory history saved successfully for {pod_name}")
            else:
                logger.error(f"Failed to generate embedding for memory history {history_id}")
        except Exception as e:
            logger.error(f"Error saving memory history: {e}")
            
        return history_id
