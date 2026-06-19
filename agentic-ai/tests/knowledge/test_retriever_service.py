"""
Tests for RetrieverService.
"""
import pytest
from unittest.mock import patch, MagicMock
from services.retrieval.retriever_service import RetrieverService

class TestRetrieverService:
    @patch("services.retrieval.retriever_service.EmbeddingService")
    @patch("services.retrieval.retriever_service.ChromaService")
    def test_retrieve_similar_incidents(self, MockChroma, MockEmbed):
        # Mock embeddings
        mock_embed_instance = MockEmbed.return_value
        mock_embed_instance.generate_embedding.return_value = [0.1] * 768
        
        # Mock chroma search response
        mock_chroma_instance = MockChroma.return_value
        mock_chroma_instance.search_incidents.return_value = {
            "ids": [["inc-1"]],
            "distances": [[0.1]], # distance = 0.1 -> similarity = 0.9
            "metadatas": [[{"severity": "CRITICAL", "root_cause": "OOM_KILLED"}]],
            "documents": [["Scale up nodes."]]
        }
        
        svc = RetrieverService()
        svc._embedding = mock_embed_instance
        svc._chroma = mock_chroma_instance
        
        incidents = svc.retrieve_similar_incidents("Some incident")
        
        assert len(incidents) == 1
        assert incidents[0].incident_id == "inc-1"
        assert incidents[0].similarity_score == 0.9
        assert incidents[0].recommendation == "Scale up nodes."
