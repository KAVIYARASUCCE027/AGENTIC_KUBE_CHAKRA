"""
Tests for EmbeddingService.
"""
import pytest
from unittest.mock import patch, MagicMock
from services.embeddings.embedding_service import EmbeddingService

class TestEmbeddingService:
    @patch("services.embeddings.embedding_service.genai.Client")
    def test_generate_embedding_success(self, MockClient):
        # Setup mock
        mock_client_instance = MockClient.return_value
        mock_response = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3]
        mock_response.embeddings = [mock_embedding]
        mock_client_instance.models.embed_content.return_value = mock_response
        
        svc = EmbeddingService()
        svc._client = mock_client_instance
        
        vector = svc.generate_embedding("Test string")
        assert vector == [0.1, 0.2, 0.3]
        mock_client_instance.models.embed_content.assert_called_once()
        
        # Test Cache hit
        vector2 = svc.generate_embedding("Test string")
        assert vector2 == [0.1, 0.2, 0.3]
        # Should not have called embed_content a second time
        assert mock_client_instance.models.embed_content.call_count == 1
