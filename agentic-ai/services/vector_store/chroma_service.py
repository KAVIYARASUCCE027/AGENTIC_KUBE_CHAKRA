"""
ChromaDB Vector Store Service — Phase 11.
"""
import os
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings

from utils.metrics import vector_search_requests_total, vector_search_failures_total

logger = logging.getLogger(__name__)

class ChromaService:
    """
    Low-level wrapper around ChromaDB client.
    Handles connections, collection initialization, and raw vector CRUD operations.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ChromaService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Determine mode based on environment variables (testing vs persistent)
        if os.environ.get("TESTING") == "true":
            logger.info("Initializing Ephemeral ChromaDB client for testing.")
            self._client = chromadb.EphemeralClient()
            self._client_type = "ephemeral"
            self._db_path = None
        else:
            db_path = os.environ.get("CHROMA_DB_PATH", "./data/chroma_db")
            
            # Phase 11.5: Ensure directory exists
            os.makedirs(db_path, exist_ok=True)
            
            logger.info(f"Initializing Persistent ChromaDB client at {db_path}.")
            self._client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
            self._client_type = "persistent"
            self._db_path = db_path

        # Initialize collections
        # We use cosine distance as our similarity metric (configured via metadata in Chroma)
        self._incidents_col = self._client.get_or_create_collection(
            name="incidents", metadata={"hnsw:space": "cosine"}
        )
        self._runbooks_col = self._client.get_or_create_collection(
            name="runbooks", metadata={"hnsw:space": "cosine"}
        )
        self._knowledge_col = self._client.get_or_create_collection(
            name="knowledge_base", metadata={"hnsw:space": "cosine"}
        )
        self._k8s_docs_col = self._client.get_or_create_collection(
            name="kubernetes_docs", metadata={"hnsw:space": "cosine"}
        )
        self._prom_guides_col = self._client.get_or_create_collection(
            name="prometheus_guides", metadata={"hnsw:space": "cosine"}
        )
        self._execution_audit_col = self._client.get_or_create_collection(
            name="execution_audit_logs", metadata={"hnsw:space": "cosine"}
        )
        self._execution_history_col = self._client.get_or_create_collection(
            name="execution_history", metadata={"hnsw:space": "cosine"}
        )
        # Phase 16
        self._memory_history_col = self._client.get_or_create_collection(
            name="memory_history", metadata={"hnsw:space": "cosine"}
        )
        self._disk_history_col = self._client.get_or_create_collection(
            name="disk_history", metadata={"hnsw:space": "cosine"}
        )
        self._network_history_col = self._client.get_or_create_collection(
            name="network_history", metadata={"hnsw:space": "cosine"}
        )
        self._log_history_col = self._client.get_or_create_collection(
            name="log_history", metadata={"hnsw:space": "cosine"}
        )
        self._event_history_col = self._client.get_or_create_collection(
            name="event_history", metadata={"hnsw:space": "cosine"}
        )
        
        # Phase 18
        self._agent_messages_col = self._client.get_or_create_collection(
            name="agent_messages", metadata={"hnsw:space": "cosine"}
        )
        self._correlated_incidents_col = self._client.get_or_create_collection(
            name="correlated_incidents", metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"ChromaService initialized. Client Type: {self._client_type}, DB Path: {self._db_path}")
        logger.info(f"Collection counts -> Incidents: {self._incidents_col.count()}, Runbooks: {self._runbooks_col.count()}, Knowledge: {self._knowledge_col.count()}, K8s Docs: {self._k8s_docs_col.count()}, Prom Guides: {self._prom_guides_col.count()}, Audit: {self._execution_audit_col.count()}, History: {self._execution_history_col.count()}")

    # --- Incidents Collection ---
    
    def add_incident(self, incident_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        """Upserts an incident vector into ChromaDB."""
        try:
            self._incidents_col.upsert(
                ids=[incident_id],
                embeddings=[vector],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"ChromaService: Successfully upserted incident {incident_id} (Total vectors: {self._incidents_col.count()}).")
        except Exception as e:
            logger.error(f"Failed to add incident to ChromaDB: {e}")
            raise

    def search_incidents(self, query_vector: List[float], severity: Optional[str] = None, root_cause: Optional[str] = None, top_k: int = 5) -> Dict:
        """Raw search on incidents collection with optional metadata filters."""
        vector_search_requests_total.labels(collection="incidents").inc()
        try:
            where_filter = {}
            if severity:
                where_filter["severity"] = severity
            if root_cause:
                where_filter["root_cause"] = root_cause
            
            # If multiple filters, we need $and syntax in Chroma
            if len(where_filter) > 1:
                where_filter = {"$and": [{k: v} for k, v in where_filter.items()]}

            results = self._incidents_col.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_filter if where_filter else None,
                include=["metadatas", "documents", "distances"]
            )
            return results
        except Exception as e:
            vector_search_failures_total.labels(collection="incidents").inc()
            logger.error(f"Failed to search incidents in ChromaDB: {e}")
            raise

    # --- Runbooks Collection ---
    
    def add_runbook(self, runbook_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        try:
            self._runbooks_col.upsert(
                ids=[runbook_id],
                embeddings=[vector],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"ChromaService: Successfully upserted runbook {runbook_id} (Total vectors: {self._runbooks_col.count()}).")
        except Exception as e:
            logger.error(f"Failed to add runbook to ChromaDB: {e}")
            raise

    def search_runbooks(self, query_vector: List[float], root_cause_target: Optional[str] = None, top_k: int = 3) -> Dict:
        vector_search_requests_total.labels(collection="runbooks").inc()
        try:
            where_filter = {"root_cause_target": root_cause_target} if root_cause_target else None
            return self._runbooks_col.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_filter,
                include=["metadatas", "documents", "distances"]
            )
        except Exception as e:
            vector_search_failures_total.labels(collection="runbooks").inc()
            logger.error(f"Failed to search runbooks in ChromaDB: {e}")
            raise

    # --- Knowledge Base Collection ---
    
    def add_document(self, doc_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        try:
            self._knowledge_col.upsert(
                ids=[doc_id],
                embeddings=[vector],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"ChromaService: Successfully upserted document {doc_id} (Total vectors: {self._knowledge_col.count()}).")
        except Exception as e:
            logger.error(f"Failed to add knowledge document to ChromaDB: {e}")
            raise

    def search_documents(self, query_vector: List[float], topic: Optional[str] = None, top_k: int = 3) -> Dict:
        vector_search_requests_total.labels(collection="knowledge_base").inc()
        try:
            where_filter = {"topic": topic} if topic else None
            return self._knowledge_col.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_filter,
                include=["metadatas", "documents", "distances"]
            )
        except Exception as e:
            vector_search_failures_total.labels(collection="knowledge_base").inc()
            logger.error(f"Failed to search knowledge base in ChromaDB: {e}")
            raise

    # --- Kubernetes Docs Collection ---
    
    def add_kubernetes_doc(self, doc_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        try:
            self._k8s_docs_col.upsert(
                ids=[doc_id],
                embeddings=[vector],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"ChromaService: Successfully upserted k8s doc {doc_id} (Total vectors: {self._k8s_docs_col.count()}).")
        except Exception as e:
            logger.error(f"Failed to add k8s doc to ChromaDB: {e}")
            raise

    def search_kubernetes_docs(self, query_vector: List[float], topic: Optional[str] = None, top_k: int = 3) -> Dict:
        vector_search_requests_total.labels(collection="kubernetes_docs").inc()
        try:
            where_filter = {"topic": topic} if topic else None
            return self._k8s_docs_col.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_filter,
                include=["metadatas", "documents", "distances"]
            )
        except Exception as e:
            vector_search_failures_total.labels(collection="kubernetes_docs").inc()
            logger.error(f"Failed to search k8s docs in ChromaDB: {e}")
            raise

    # --- Prometheus Guides Collection ---
    
    def add_prometheus_guide(self, guide_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        try:
            self._prom_guides_col.upsert(
                ids=[guide_id],
                embeddings=[vector],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"ChromaService: Successfully upserted prometheus guide {guide_id} (Total vectors: {self._prom_guides_col.count()}).")
        except Exception as e:
            logger.error(f"Failed to add prometheus guide to ChromaDB: {e}")
            raise

    def search_prometheus_guides(self, query_vector: List[float], topic: Optional[str] = None, top_k: int = 3) -> Dict:
        vector_search_requests_total.labels(collection="prometheus_guides").inc()
        try:
            where_filter = {"topic": topic} if topic else None
            return self._prom_guides_col.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_filter,
                include=["metadatas", "documents", "distances"]
            )
        except Exception as e:
            vector_search_failures_total.labels(collection="prometheus_guides").inc()
            logger.error(f"Failed to search prometheus guides in ChromaDB: {e}")
            raise

    # --- Execution Collections ---
    
    def add_execution_audit(self, audit_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        """Upserts an execution audit log into ChromaDB."""
        try:
            self._execution_audit_col.upsert(
                ids=[audit_id],
                embeddings=[vector],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"ChromaService: Successfully upserted audit log {audit_id}.")
        except Exception as e:
            logger.error(f"Failed to add audit log to ChromaDB: {e}")
            raise

    def add_execution_history(self, history_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        """Upserts an execution history record into ChromaDB."""
        try:
            self._execution_history_col.upsert(
                ids=[history_id],
                embeddings=[vector],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"ChromaService: Successfully upserted execution history {history_id}.")
        except Exception as e:
            logger.error(f"Failed to add execution history to ChromaDB: {e}")
            raise

    # --- Phase 16 Multi-Resource History Collections ---
    
    def _add_to_history(self, collection, history_id: str, document: str, metadata: Dict[str, Any], vector: List[float], name: str):
        try:
            collection.upsert(
                ids=[history_id],
                embeddings=[vector],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"ChromaService: Successfully upserted {name} history {history_id}.")
        except Exception as e:
            logger.error(f"Failed to add {name} history to ChromaDB: {e}")
            raise

    def add_memory_history(self, history_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        self._add_to_history(self._memory_history_col, history_id, document, metadata, vector, "memory")

    def add_disk_history(self, history_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        self._add_to_history(self._disk_history_col, history_id, document, metadata, vector, "disk")

    def add_network_history(self, history_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        self._add_to_history(self._network_history_col, history_id, document, metadata, vector, "network")

    def add_log_history(self, history_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        self._add_to_history(self._log_history_col, history_id, document, metadata, vector, "log")

    def add_event_history(self, history_id: str, document: str, metadata: Dict[str, Any], vector: List[float]):
        self._add_to_history(self._event_history_col, history_id, document, metadata, vector, "event")
