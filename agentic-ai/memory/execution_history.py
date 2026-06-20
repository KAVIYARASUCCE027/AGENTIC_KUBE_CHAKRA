"""
Execution History Memory — Phase 15.
"""
import uuid
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from services.vector_store.chroma_service import ChromaService
from services.embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class ExecutionHistoryMemory:
    """
    Maintains execution memory for previous incidents.
    """
    def __init__(self):
        self._chroma = ChromaService()
        self._embedding = EmbeddingService()

    def add_history(self, incident_id: str, action: str, result: str, rollback_reference: str = "") -> str:
        """
        Stores the historical result of an execution.
        """
        history_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        document = f"Execution History for {incident_id}: Action '{action}' resulted in '{result}'."
        metadata = {
            "incident_id": incident_id,
            "action": action,
            "result": result,
            "timestamp": timestamp,
            "rollback_reference": rollback_reference
        }
        
        try:
            vector = self._embedding.generate_embedding(document)
            if vector:
                self._chroma.add_execution_history(history_id, document, metadata, vector)
                logger.info(f"Execution history saved successfully for incident {incident_id}")
            else:
                logger.error(f"Failed to generate embedding for execution history {history_id}")
        except Exception as e:
            logger.error(f"Error saving execution history: {e}")
            
        return history_id
