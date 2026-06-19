"""
Gemini Correlation Service — Phase 12.

Uses the native google.genai SDK (google-genai package) to call
gemini-2.5-flash for multi-signal event correlation.

Follows the identical structural pattern established by
GeminiRootCauseService (Phase 6):
  - Build the prompt via CorrelationPromptBuilder
  - Call Gemini with production-grade generation config
  - Parse and validate the JSON response
  - Return a fully-populated CorrelationOutput
  - Retry up to 2 times on transient failures
  - Return a safe fallback on exhausted retries

The caller (CorrelationAgent) is responsible for injecting the
pre-built RAG context from ChromaDB before invoking this service.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

from google import genai
from google.genai import types as genai_types

from config.settings import get_settings
from enums.incident_type import IncidentType
from enums.correlation_source import CorrelationSource
from schemas.cpu_state import CPUState
from schemas.correlation.correlation_output import CorrelationOutput
from schemas.correlation.correlated_event import CorrelatedEvent
from prompts.correlation_prompt_builder import CorrelationPromptBuilder

logger = logging.getLogger(__name__)

_MODEL_NAME      = "gemini-2.5-flash"
_TEMPERATURE     = 0.1
_TOP_P           = 0.8
_TOP_K           = 20
_MAX_OUT_TOKENS  = 800
_MAX_RETRIES     = 2

_FALLBACK_OUTPUT = CorrelationOutput(
    incident_type=IncidentType.UNKNOWN,
    root_cause="Correlation analysis unavailable — Gemini API call failed.",
    confidence_score=0.0,
    evidence=["Gemini API call failed after retries."],
    correlation_summary="Unable to correlate signals due to an AI service failure.",
    correlated_events=[],
    source=CorrelationSource.FALLBACK,
    model_name=_MODEL_NAME,
)

# Valid incident type strings for validation
_VALID_INCIDENT_TYPES = {it.value for it in IncidentType}


class GeminiCorrelationService:
    """
    Production-grade Gemini-powered multi-signal Event Correlation service.

    Consumes all six signal summaries from CPUState plus optional RAG
    context from ChromaDB, then returns a CorrelationOutput with an
    AI-determined incident type, root cause, and confidence score.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Cannot initialise GeminiCorrelationService."
            )
        self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self._prompt_builder = CorrelationPromptBuilder()
        logger.info(
            "GeminiCorrelationService initialised with model %s.", _MODEL_NAME
        )

    def correlate(
        self,
        state: CPUState,
        rag_context: str = "",
        existing_events: Optional[list[CorrelatedEvent]] = None,
    ) -> CorrelationOutput:
        """
        Run multi-signal correlation via Gemini with retry logic.

        Args:
            state:           Current CPUState containing all signal summaries.
            rag_context:     Pre-built RAG context from ChromaDB (may be empty).
            existing_events: CorrelatedEvents already built by the rule engine
                             (reused to avoid duplication in the output).

        Returns:
            CorrelationOutput — either Gemini result or safe fallback.
        """
        historical_match = bool(rag_context and rag_context.strip())

        system_prompt, user_prompt = self._prompt_builder.build(
            pod_name=state.inputs.pod_name,
            namespace=state.inputs.namespace,
            cpu_analysis=state.cpu_analysis or self._default_cpu_summary(state),
            memory_analysis=state.memory_analysis or "No memory signal available.",
            disk_analysis=state.disk_analysis or "No disk signal available.",
            network_analysis=state.network_analysis or "No network signal available.",
            log_analysis=state.log_analysis or "No log signal available.",
            event_analysis=state.event_analysis or "No Kubernetes events available.",
            historical_context=rag_context,
        )

        logger.info(
            "GeminiCorrelationService: Sending correlation request for %s/%s.",
            state.inputs.namespace,
            state.inputs.pod_name,
        )

        last_error: Optional[Exception] = None
        for attempt in range(1, _MAX_RETRIES + 2):
            try:
                start = time.monotonic()
                response = self._client.models.generate_content(
                    model=_MODEL_NAME,
                    contents=user_prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=_TEMPERATURE,
                        top_p=_TOP_P,
                        top_k=_TOP_K,
                        max_output_tokens=_MAX_OUT_TOKENS,
                    ),
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                raw_text = response.text or ""

                logger.debug(
                    "GeminiCorrelationService: Raw response (attempt %d): %s",
                    attempt,
                    raw_text[:300],
                )

                parsed = self._parse_response(raw_text)

                # Build output
                output = CorrelationOutput(
                    incident_type=IncidentType(
                        parsed.get("incident_type", "UNKNOWN")
                    ),
                    root_cause=parsed.get("root_cause", ""),
                    confidence_score=float(
                        min(1.0, max(0.0, parsed.get("confidence_score", 0.0)))
                    ),
                    evidence=parsed.get("evidence", []),
                    correlation_summary=parsed.get("correlation_summary", ""),
                    correlated_events=existing_events or [],
                    source=CorrelationSource.GEMINI,
                    model_name=_MODEL_NAME,
                    execution_time_ms=elapsed_ms,
                    historical_match=historical_match,
                    historical_context=rag_context if historical_match else None,
                )

                logger.info(
                    "GeminiCorrelationService: Result — incident=%s confidence=%.2f source=%s",
                    output.incident_type.value,
                    output.confidence_score,
                    output.source.value,
                )
                return output

            except Exception as exc:
                last_error = exc
                if attempt <= _MAX_RETRIES:
                    logger.warning(
                        "GeminiCorrelationService: Attempt %d/%d failed: %s. Retrying...",
                        attempt,
                        _MAX_RETRIES + 1,
                        exc,
                    )
                else:
                    logger.error(
                        "GeminiCorrelationService: All %d attempts failed. Last error: %s",
                        _MAX_RETRIES + 1,
                        exc,
                        exc_info=True,
                    )

        return _FALLBACK_OUTPUT

    # ─────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(raw_text: str) -> dict:
        """
        Extract and validate the JSON object from the Gemini response.

        Handles markdown code fences (```json ... ```) that Gemini sometimes
        wraps its response in, even when instructed not to.

        Raises:
            ValueError: If JSON is missing required fields or contains
                        an unknown incident_type.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE).strip()
        cleaned = cleaned.rstrip("`").strip()

        # Extract JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError(
                f"No JSON object found in Gemini response: {raw_text[:200]}"
            )

        data: dict = json.loads(match.group())

        # Validate required fields
        required = {"incident_type", "root_cause", "confidence_score"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Gemini response missing required fields: {missing}")

        # Normalise incident_type
        raw_incident = str(data.get("incident_type", "UNKNOWN")).upper().strip()
        if raw_incident not in _VALID_INCIDENT_TYPES:
            logger.warning(
                "GeminiCorrelationService: Unknown incident_type '%s', defaulting to UNKNOWN.",
                raw_incident,
            )
            data["incident_type"] = "UNKNOWN"
        else:
            data["incident_type"] = raw_incident

        # Ensure lists
        for list_field in ("evidence",):
            if not isinstance(data.get(list_field), list):
                data[list_field] = []

        return data

    @staticmethod
    def _default_cpu_summary(state: CPUState) -> str:
        """Produce a compact CPU summary when cpu_analysis is not pre-populated."""
        m = state.metrics
        return (
            f"CPU usage: {m.cpu_usage:.1f}%, "
            f"Throttling: {m.throttling_percentage:.1f}%, "
            f"Restarts: {m.restart_count}, "
            f"Trend: {m.cpu_trend.value}."
        )
