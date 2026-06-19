"""
Knowledge Ingestion Service — Phase 13.
"""
import logging
import hashlib
from typing import List

from services.knowledge.document_loader_service import DocumentLoaderService
from services.embeddings.embedding_service import EmbeddingService
from services.vector_store.chroma_service import ChromaService

logger = logging.getLogger(__name__)

class KnowledgeIngestionService:
    """
    Ingests local markdown documents, chunks them, generates embeddings,
    and stores them in the appropriate ChromaDB collections.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self._loader = DocumentLoaderService()
        self._embedding_service = EmbeddingService()
        self._chroma = ChromaService()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def ingest_all(self) -> dict:
        """
        Loads all documents and ingests them. Returns stats.
        """
        docs = self._loader.load_all_documents()
        stats = {
            "runbooks": 0,
            "kubernetes_docs": 0,
            "prometheus_guides": 0,
            "knowledge_base": 0,
            "total_chunks": 0
        }
        
        for doc in docs:
            chunks = self._chunk_text(doc["content"])
            for idx, chunk in enumerate(chunks):
                # We need a stable ID for incremental upserts
                chunk_id = self._generate_chunk_id(doc["source"], idx, chunk)
                
                # Generate embedding
                vector = self._embedding_service.generate_embedding(chunk)
                if not vector:
                    logger.warning(f"Failed to generate embedding for chunk {chunk_id}")
                    continue
                    
                metadata = {
                    "source": doc["source"],
                    "title": doc["title"],
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "topic": doc["title"] # Used for searching
                }
                
                cat = doc["category"]
                if cat == "runbooks":
                    # For runbooks, we map title to root_cause_target to match existing schema
                    metadata["root_cause_target"] = doc["title"]
                    self._chroma.add_runbook(chunk_id, chunk, metadata, vector)
                    stats["runbooks"] += 1
                elif cat == "kubernetes_docs":
                    self._chroma.add_kubernetes_doc(chunk_id, chunk, metadata, vector)
                    stats["kubernetes_docs"] += 1
                elif cat == "prometheus_guides":
                    self._chroma.add_prometheus_guide(chunk_id, chunk, metadata, vector)
                    stats["prometheus_guides"] += 1
                else:
                    self._chroma.add_document(chunk_id, chunk, metadata, vector)
                    stats["knowledge_base"] += 1
                    
                stats["total_chunks"] += 1
                
        logger.info(f"Ingestion complete. Stats: {stats}")
        return stats

    def _chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks of `chunk_size` with `chunk_overlap`.
        Basic sliding window approach.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunks.append(text[start:end])
            if end >= text_length:
                break
            # Move forward by (size - overlap)
            start += (self.chunk_size - self.chunk_overlap)
            
        return chunks

    def _generate_chunk_id(self, source: str, index: int, chunk_text: str) -> str:
        """
        Generates a stable ID for a chunk to allow incremental updates (upserts).
        """
        # A hash of the source + index + content ensures that if the content changes, 
        # it might create a new chunk, but typically we want it stable by source+index.
        # For true incremental, using just source + index is better so we overwrite.
        raw_id = f"{source}::chunk_{index}"
        return hashlib.md5(raw_id.encode('utf-8')).hexdigest()
