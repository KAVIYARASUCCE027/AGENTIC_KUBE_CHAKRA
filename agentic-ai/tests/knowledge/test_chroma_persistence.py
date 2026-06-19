"""
Test Chroma persistence explicitly.
"""
import pytest
import os
import shutil
from services.vector_store.chroma_service import ChromaService

@pytest.fixture
def temp_db_path():
    path = "./data/test_chroma_db"
    # Ensure clean slate
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
    
    # Remove TESTING env var to force PersistentClient
    old_testing = os.environ.get("TESTING")
    os.environ.pop("TESTING", None)
    os.environ["CHROMA_DB_PATH"] = path
    
    # We must reset the singleton to test initialization
    ChromaService._instance = None
    
    yield path
    
    # Cleanup
    if old_testing is not None:
        os.environ["TESTING"] = old_testing
    else:
        os.environ.pop("TESTING", None)
    
    ChromaService._instance = None
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

class TestChromaPersistence:
    def test_chroma_creates_directory_and_persists(self, temp_db_path):
        # 1. Initialize
        chroma = ChromaService()
        
        # 2. Check directory was created
        assert os.path.exists(temp_db_path)
        assert chroma._client_type == "persistent"
        
        # 3. Add an incident
        vector = [0.1] * 768
        chroma.add_incident(
            incident_id="inc-persistence",
            document="Test document",
            metadata={"severity": "CRITICAL", "root_cause": "OOM_KILLED"},
            vector=vector
        )
        
        # 4. Re-initialize to simulate restart
        ChromaService._instance = None
        chroma2 = ChromaService()
        
        # 5. Search for the incident
        search_vec = [0.1] * 768
        results = chroma2.search_incidents(search_vec, severity="CRITICAL", top_k=1)
        
        # Data should survive the restart
        assert "inc-persistence" in results["ids"][0]
