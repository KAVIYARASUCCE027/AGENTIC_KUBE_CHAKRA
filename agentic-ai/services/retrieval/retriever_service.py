"""
Retriever Service — Phase 11.
"""
import time
import logging
from typing import List, Optional

from services.vector_store.chroma_service import ChromaService
from services.embeddings.embedding_service import EmbeddingService
from schemas.knowledge.chroma_schemas import ChromaIncident, ChromaRunbook, KnowledgeDocument
from utils.metrics import retrieval_latency_seconds, similar_incidents_found_total

logger = logging.getLogger(__name__)

class RetrieverService:
    """
    High-level RAG service that fetches semantic matches from ChromaDB
    and maps raw results into strongly typed models.
    """
    def __init__(self):
        self._chroma = ChromaService()
        self._embedding = EmbeddingService()
        # Cosine distance in Chroma: 0 is exact match, higher is less similar.
        # So similarity_score can be approximated as 1.0 - distance
        self._similarity_threshold = 0.35 # (Meaning distance <= 0.35)

    def retrieve_similar_incidents(
        self, incident_signature: str, severity: Optional[str] = None, root_cause: Optional[str] = None
    ) -> List[ChromaIncident]:
        start_t = time.perf_counter()
        results_out = []
        try:
            vector = self._embedding.generate_embedding(incident_signature)
            if not vector:
                return []

            raw_results = self._chroma.search_incidents(vector, severity=severity, root_cause=root_cause, top_k=5)
            
            if not raw_results or not raw_results['ids']:
                return []

            for i in range(len(raw_results['ids'][0])):
                distance = raw_results['distances'][0][i]
                if distance > self._similarity_threshold:
                    continue # Skip low similarity
                
                doc = raw_results['documents'][0][i]
                meta = raw_results['metadatas'][0][i]
                
                results_out.append(ChromaIncident(
                    incident_id=meta.get("incident_id", raw_results['ids'][0][i]),
                    severity=meta.get("severity", "UNKNOWN"),
                    root_cause=meta.get("root_cause", "UNKNOWN"),
                    similarity_score=max(0.0, 1.0 - distance),
                    recommendation=doc  # Assuming doc holds the recommendation/summary
                ))
            
            similar_incidents_found_total.inc(len(results_out))
            
        except Exception as e:
            logger.warning(f"RetrieverService failed to fetch incidents: {e}")
        finally:
            retrieval_latency_seconds.labels(collection="incidents").observe(time.perf_counter() - start_t)
            
        return results_out

    def retrieve_runbooks(self, root_cause: str) -> List[ChromaRunbook]:
        start_t = time.perf_counter()
        results_out = []
        try:
            # We embed the root cause string directly to find relevant runbooks
            vector = self._embedding.generate_embedding(root_cause)
            if not vector:
                return []

            raw_results = self._chroma.search_runbooks(vector, root_cause_target=root_cause, top_k=3)
            
            if not raw_results or not raw_results['ids']:
                return []

            for i in range(len(raw_results['ids'][0])):
                distance = raw_results['distances'][0][i]
                if distance > self._similarity_threshold:
                    continue
                
                doc = raw_results['documents'][0][i]
                meta = raw_results['metadatas'][0][i]
                
                results_out.append(ChromaRunbook(
                    runbook_id=raw_results['ids'][0][i],
                    root_cause_target=meta.get("root_cause_target", "UNKNOWN"),
                    similarity_score=max(0.0, 1.0 - distance),
                    action_plan=doc
                ))
        except Exception as e:
            logger.warning(f"RetrieverService failed to fetch runbooks: {e}")
        finally:
            retrieval_latency_seconds.labels(collection="runbooks").observe(time.perf_counter() - start_t)
            
        return results_out

    def retrieve_documents(self, search_query: str, topic: Optional[str] = None) -> List[KnowledgeDocument]:
        start_t = time.perf_counter()
        results_out = []
        try:
            vector = self._embedding.generate_embedding(search_query)
            if not vector:
                return []

            raw_results = self._chroma.search_documents(vector, topic=topic, top_k=3)
            
            if not raw_results or not raw_results['ids']:
                return []

            for i in range(len(raw_results['ids'][0])):
                distance = raw_results['distances'][0][i]
                if distance > self._similarity_threshold:
                    continue
                
                doc = raw_results['documents'][0][i]
                meta = raw_results['metadatas'][0][i]
                
                results_out.append(KnowledgeDocument(
                    doc_id=raw_results['ids'][0][i],
                    topic=meta.get("topic", "UNKNOWN"),
                    source=meta.get("source", "UNKNOWN"),
                    similarity_score=max(0.0, 1.0 - distance),
                    content=doc
                ))
        except Exception as e:
            logger.warning(f"RetrieverService failed to fetch knowledge docs: {e}")
        finally:
            retrieval_latency_seconds.labels(collection="knowledge_base").observe(time.perf_counter() - start_t)
            
        return results_out
