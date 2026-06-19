"""
Gemini Knowledge Service — Phase 13.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types as genai_types

from config.settings import get_settings
from schemas.knowledge.knowledge_chunk import KnowledgeChunk
from schemas.knowledge.knowledge_response import KnowledgeResponse

logger = logging.getLogger(__name__)

_MODEL_NAME      = "gemini-2.5-flash"
_TEMPERATURE     = 0.2
_TOP_P           = 0.8
_TOP_K           = 20
_MAX_OUT_TOKENS  = 1500
_MAX_RETRIES     = 2

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

class GeminiKnowledgeService:
    """
    Production-grade AI service for answering SRE questions using
    retrieved knowledge chunks via Gemini.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Cannot initialise GeminiKnowledgeService."
            )
        self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self._system_prompt = self._load_prompt("knowledge_system_prompt.txt")
        self._user_template = self._load_prompt("knowledge_prompt.txt")
        logger.info(
            "GeminiKnowledgeService initialised with model %s.", _MODEL_NAME
        )

    def answer_question(self, question: str, chunks: List[KnowledgeChunk]) -> KnowledgeResponse:
        """
        Ask Gemini to answer the question using the retrieved chunks.
        """
        start = time.monotonic()
        
        # Calculate overall confidence from chunks
        avg_confidence = 0.0
        if chunks:
            avg_confidence = sum(c.score for c in chunks) / len(chunks)
            
        # Build context string
        context_str = self._build_context_string(chunks)
        
        # Format user prompt
        user_prompt = self._user_template.format(
            question=question,
            context=context_str
        )
        
        logger.info(f"GeminiKnowledgeService: Asking question -> '{question}' with {len(chunks)} context chunks.")

        for attempt in range(1, _MAX_RETRIES + 2):
            try:
                response = self._client.models.generate_content(
                    model=_MODEL_NAME,
                    contents=user_prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=self._system_prompt,
                        temperature=_TEMPERATURE,
                        top_p=_TOP_P,
                        top_k=_TOP_K,
                        max_output_tokens=_MAX_OUT_TOKENS,
                    ),
                )
                
                elapsed_ms = int((time.monotonic() - start) * 1000)
                raw_text = response.text or ""
                
                parsed = self._parse_response(raw_text)
                
                # Combine Gemini's confidence with the retrieval confidence
                # If Gemini is very confident but retrieval was poor, scale it down.
                gemini_conf = float(parsed.get("confidence_score", 0.0))
                final_conf = (gemini_conf + avg_confidence) / 2 if chunks else gemini_conf
                
                output = KnowledgeResponse(
                    answer=parsed.get("answer", "No answer generated."),
                    sources=chunks,
                    confidence_score=round(final_conf, 3),
                    model_name=_MODEL_NAME,
                    execution_time_ms=elapsed_ms,
                    timestamp=datetime.now(timezone.utc)
                )
                
                logger.info(f"GeminiKnowledgeService: Generated answer in {elapsed_ms}ms with confidence {output.confidence_score}.")
                return output
                
            except Exception as exc:
                if attempt <= _MAX_RETRIES:
                    logger.warning(
                        "GeminiKnowledgeService: Attempt %d/%d failed: %s. Retrying...",
                        attempt,
                        _MAX_RETRIES + 1,
                        exc,
                    )
                else:
                    logger.error(
                        "GeminiKnowledgeService: All %d attempts failed. Last error: %s",
                        _MAX_RETRIES + 1,
                        exc,
                        exc_info=True,
                    )
                    
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return KnowledgeResponse(
            answer="Failed to generate an answer due to an AI service error. Please try again later.",
            sources=chunks,
            confidence_score=0.0,
            model_name=_MODEL_NAME,
            execution_time_ms=elapsed_ms,
            timestamp=datetime.now(timezone.utc)
        )

    # ─────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────

    def _build_context_string(self, chunks: List[KnowledgeChunk]) -> str:
        if not chunks:
            return "NO RETRIEVED KNOWLEDGE FOUND."
            
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"--- SOURCE [{i}] ---\n"
                f"Collection: {chunk.collection}\n"
                f"Origin: {chunk.source}\n"
                f"Relevance Score: {chunk.score:.2f}\n"
                f"Content:\n{chunk.content}\n"
            )
        return "\n".join(parts)

    @staticmethod
    def _parse_response(raw_text: str) -> dict:
        """
        Extract and validate the JSON object from the Gemini response.
        """
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE).strip()
        cleaned = cleaned.rstrip("`").strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError(
                f"No JSON object found in Gemini response: {raw_text[:200]}"
            )

        data: dict = json.loads(match.group())

        required = {"answer"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Gemini response missing required fields: {missing}")

        return data

    @staticmethod
    def _load_prompt(filename: str) -> str:
        filepath = _PROMPTS_DIR / filename
        try:
            with filepath.open(encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            logger.error("Failed to load prompt %s: %s", filepath, e)
            return ""
