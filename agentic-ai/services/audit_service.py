"""
Audit Service — Phase 15.
"""
import uuid
from typing import Dict, Any
from datetime import datetime, timezone
import logging

from services.vector_store.chroma_service import ChromaService
from services.embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class AuditService:
    """
    Stores execution records in ChromaDB.
    """
    def __init__(self):
        self._chroma = ChromaService()
        self._embedding = EmbeddingService()

    def log_execution(
        self, 
        incident_id: str, 
        action_type: str, 
        command: str, 
        status: str, 
        executed_by: str, 
        rollback_reference: str = ""
    ) -> str:
        """
        Logs the execution details to the execution_audit_logs collection.
        Returns the generated audit ID.
        """
        audit_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        document = f"Execution Audit [{status}]: {action_type} ran command '{command}' on incident {incident_id} at {timestamp}."
        metadata = {
            "incident_id": incident_id,
            "action_type": action_type,
            "command": command,
            "status": status,
            "executed_by": executed_by,
            "timestamp": timestamp,
            "rollback_reference": rollback_reference
        }
        
        try:
            vector = self._embedding.generate_embedding(document)
            if vector:
                self._chroma.add_execution_audit(audit_id, document, metadata, vector)
                logger.info(f"Audit log saved successfully for incident {incident_id}")
            else:
                logger.error(f"Failed to generate embedding for audit log {audit_id}")
        except Exception as e:
            logger.error(f"Error saving audit log: {e}")
            
        return audit_id
