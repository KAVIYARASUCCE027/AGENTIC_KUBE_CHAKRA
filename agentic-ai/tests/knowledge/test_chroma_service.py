"""
Tests for ChromaService.
"""
import pytest
import os
from services.vector_store.chroma_service import ChromaService

@pytest.fixture(autouse=True)
def setup_ephemeral_db():
    os.environ["TESTING"] = "true"
    yield
    os.environ.pop("TESTING", None)

class TestChromaService:
    def test_incident_upsert_and_search(self):
        chroma = ChromaService()
        
        # Add an incident
        vector = [0.1] * 768  # mock 768-dim vector
        chroma.add_incident(
            incident_id="inc-123",
            document="Restart the pod immediately.",
            metadata={"severity": "CRITICAL", "root_cause": "OOM_KILLED"},
            vector=vector
        )
        
        # Search it back
        search_vec = [0.1] * 768
        results = chroma.search_incidents(search_vec, severity="CRITICAL", top_k=1)
        
        assert "inc-123" in results["ids"][0]
        assert results["metadatas"][0][0]["root_cause"] == "OOM_KILLED"
        assert results["documents"][0][0] == "Restart the pod immediately."
