"""
Knowledge Retriever Service — Phase 13.
"""
import time
import logging
from typing import List

from services.vector_store.chroma_service import ChromaService
from services.embeddings.embedding_service import EmbeddingService
from schemas.knowledge.knowledge_chunk import KnowledgeChunk

logger = logging.getLogger(__name__)

class KnowledgeRetrieverService:
    """
    Retrieves semantic matches from across all ChromaDB collections
    to answer arbitrary SRE questions.
    """
    
    def __init__(self):
        self._chroma = ChromaService()
        self._embedding = EmbeddingService()
        # Only include results with distance <= 0.40 (score >= 0.60 roughly)
        self._similarity_threshold = 0.40 

    def retrieve(self, question: str, top_k: int = 3, include_incidents: bool = True) -> List[KnowledgeChunk]:
        """
        Embeds the question, searches all configured collections,
        and returns a deduplicated, sorted list of the best chunks.
        """
        start_t = time.perf_counter()
        results: List[KnowledgeChunk] = []
        
        try:
            vector = self._embedding.generate_embedding(question)
            if not vector:
                return []
                
            # Search each collection
            # 1. Knowledge Base (General Docs)
            raw_kb = self._chroma.search_documents(vector, top_k=top_k)
            results.extend(self._parse_raw_results(raw_kb, "knowledge_base"))
            
            # 2. Runbooks
            raw_rb = self._chroma.search_runbooks(vector, top_k=top_k)
            results.extend(self._parse_raw_results(raw_rb, "runbooks"))
            
            # 3. Kubernetes Docs
            raw_k8s = self._chroma.search_kubernetes_docs(vector, top_k=top_k)
            results.extend(self._parse_raw_results(raw_k8s, "kubernetes_docs"))
            
            # 4. Prometheus Guides
            raw_prom = self._chroma.search_prometheus_guides(vector, top_k=top_k)
            results.extend(self._parse_raw_results(raw_prom, "prometheus_guides"))
            
            # 5. Historical Incidents (Optional)
            if include_incidents:
                raw_inc = self._chroma.search_incidents(vector, top_k=top_k)
                results.extend(self._parse_raw_results(raw_inc, "incidents"))
                
            # Sort by score descending
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Remove exact duplicates (sometimes same content ingested in different chunks if overlap)
            unique_results = []
            seen_content = set()
            for r in results:
                if r.content not in seen_content:
                    seen_content.add(r.content)
                    unique_results.append(r)
                    
            # Return overall top_k across all collections
            # If top_k is 5, we might have up to 25 results before this slice.
            # But the user asked for top_k per collection in the prompt. Let's return total top K*2
            # to give the LLM enough context without blowing context window.
            final_results = unique_results[:(top_k * 2)]
            
            logger.info(f"Retrieved {len(final_results)} relevant chunks in {(time.perf_counter() - start_t)*1000:.1f}ms")
            return final_results
            
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {e}")
            return []

    def _parse_raw_results(self, raw_results: dict, collection_name: str) -> List[KnowledgeChunk]:
        """
        Helper to map Chroma raw dictionary response into KnowledgeChunk models.
        """
        chunks = []
        if not raw_results or not raw_results.get('ids') or not raw_results['ids'][0]:
            return chunks
            
        for i in range(len(raw_results['ids'][0])):
            distance = raw_results['distances'][0][i]
            if distance > self._similarity_threshold:
                continue
                
            doc = raw_results['documents'][0][i]
            meta = raw_results['metadatas'][0][i]
            
            # Similarity score approximation (Chroma cosine distance: 0 is perfect, 2 is opposite)
            score = max(0.0, 1.0 - distance)
            
            # Extract source
            source = meta.get("source", "")
            if not source:
                source = meta.get("incident_id", "")
            if not source:
                source = meta.get("runbook_id", "")
                
            chunks.append(KnowledgeChunk(
                content=doc,
                source=source or "unknown",
                collection=collection_name,
                score=score,
                metadata=meta
            ))
            
        return chunks
