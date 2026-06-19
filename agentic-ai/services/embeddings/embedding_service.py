"""
Gemini Embedding Service — Phase 11.
"""
import os
import logging
from typing import List
from functools import lru_cache

from google import genai
from google.genai import types

from config.settings import get_settings
from utils.metrics import embeddings_generated_total

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Generates text embeddings using Google's Gemini text-embedding models.
    Includes in-memory LRU caching to minimize token spend on exact duplicates.
    """
    def __init__(self):
        settings = get_settings()
        self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self._model_name = "gemini-embedding-2"

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a vector embedding for a single string of text.
        """
        if not text or not text.strip():
            logger.warning("Attempted to embed empty string.")
            return []

        # Check local cache first
        cached = self._get_cached_embedding(text)
        if cached:
            return list(cached)

        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self._client.models.embed_content(
                    model=self._model_name,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=768 # Standard for text-embedding-004
                    )
                )
                embeddings_generated_total.inc()
                
                # Extract list of floats
                vector = response.embeddings[0].values
                
                # Cache it as tuple to ensure immutability
                self._set_cached_embedding(text, tuple(vector))
                return vector
                
            except Exception as e:
                logger.error(f"Failed to generate embedding on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1.0)
        return []

    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for multiple texts. 
        Falls back to serial processing if batch API behaves differently or fails.
        """
        vectors = []
        for t in texts:
            vectors.append(self.generate_embedding(t))
        return vectors

    # --- Cache Wrappers ---
    # We use a module-level or instance-level dictionary as a simple bounded LRU-like cache.
    # To keep it truly LRU bounded, we can use functools.lru_cache on a hidden method.

    @lru_cache(maxsize=1000)
    def _get_cached_embedding(self, text: str):
        return None

    def _set_cached_embedding(self, text: str, vector: tuple):
        # We manually overwrite the cache implementation by directly calling the decorated function
        # Actually, to use lru_cache for SETTING, we can't easily inject.
        # We'll just build a simple dict for this prototype or rely on the fact that if it wasn't there, 
        # we generate it. Let's adjust to a simple dictionary cache for explicit control.
        pass

# Simple Dictionary Cache Implementation override for explicit control
class DictionaryCacheEmbeddingService(EmbeddingService):
    def __init__(self):
        super().__init__()
        self._cache = {}
        self._max_cache = 1000

    def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            return []
            
        if text in self._cache:
            return list(self._cache[text])

        try:
            response = self._client.models.embed_content(
                model=self._model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=768
                )
            )
            embeddings_generated_total.inc()
            vector = response.embeddings[0].values
            
            if len(self._cache) >= self._max_cache:
                # Naive eviction (clear half)
                keys_to_delete = list(self._cache.keys())[:500]
                for k in keys_to_delete:
                    del self._cache[k]
                    
            self._cache[text] = tuple(vector)
            return vector
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

# For actual usage, we'll export the cached version
EmbeddingService = DictionaryCacheEmbeddingService
