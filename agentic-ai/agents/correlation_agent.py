"""
Correlation Agent — Phase 12.

Implements the BaseAgent interface for the Event Correlation Engine.
Sits in the LangGraph pipeline between the metric_collector node and
the analyzer node, enriching the shared CPUState with a multi-signal
incident classification before downstream agents run.

Execution strategy (hybrid):
  1. Build free-text signal summaries from CPUState and populate the
     six signal analysis fields (cpu_analysis, memory_analysis, etc.).
  2. Call EventCorrelationService for a fast, deterministic rule match.
  3. If rule confidence >= 0.70 and incident != UNKNOWN → accept rule result.
  4. Otherwise:
     a. Query ChromaDB via RetrieverService for historical incidents.
     b. Call GeminiCorrelationService with the rule result + RAG context.
     c. Pick the higher-confidence result and mark source=HYBRID if both
        contributed.
  5. Write the final CorrelationOutput back to CPUState.
"""
from __future__ import annotations

import logging
import time

from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from schemas.correlation.correlation_output import CorrelationOutput
from enums.incident_type import IncidentType
from enums.correlation_source import CorrelationSource
from services.correlation.event_correlation_service import EventCorrelationService
from services.gemini.gemini_correlation_service import GeminiCorrelationService
from services.retrieval.retriever_service import RetrieverService
from services.retrieval.context_builder import ContextBuilder

logger = logging.getLogger(__name__)

# Minimum rule-based confidence to skip the Gemini call
_RULE_CONFIDENCE_THRESHOLD = 0.70


class CorrelationAgent(BaseAgent):
    """
    Multi-signal Event Correlation Agent.

    Fuses CPU, Memory, Disk, Network, Log, and Kubernetes Event signals
    to identify the most probable incident type and its root cause.

    Registered under the name 'correlation' in AgentRegistry.
    """

    def __init__(self) -> None:
        self._rule_service   = EventCorrelationService()
        self._gemini_service = GeminiCorrelationService()
        self._retriever      = RetrieverService()
        self._ctx_builder    = ContextBuilder()
        logger.info("CorrelationAgent: Initialised (rule + Gemini + RAG).")

    @property
    def name(self) -> str:
        return "correlation"

    # ─────────────────────────────────────────────────────────────────────
    # BaseAgent interface
    # ─────────────────────────────────────────────────────────────────────

    def execute(self, state: CPUState) -> CPUState:
        """
        Run the hybrid event correlation pipeline.

        Args:
            state: Current shared CPUState — reads metrics, writes
                   cpu_analysis / memory_analysis / … / correlation_output.

        Returns:
            Updated CPUState with correlation_output and signal fields set.
        """
        start_t = time.perf_counter()
        logger.info(
            "CorrelationAgent: Starting correlation for %s/%s.",
            state.inputs.namespace,
            state.inputs.pod_name,
        )

        # ── Step 1: Build signal summaries ────────────────────────────
        updated_state = self._populate_signal_fields(state)

        # ── Step 2: Rule-based correlation ────────────────────────────
        rule_output: CorrelationOutput = self._rule_service.correlate(updated_state)
        logger.info(
            "CorrelationAgent: Rule engine → incident=%s confidence=%.2f",
            rule_output.incident_type.value,
            rule_output.confidence_score,
        )

        # ── Step 3: Decide whether Gemini is needed ────────────────────
        needs_gemini = (
            rule_output.incident_type == IncidentType.UNKNOWN
            or rule_output.confidence_score < _RULE_CONFIDENCE_THRESHOLD
        )

        final_output: CorrelationOutput

        if not needs_gemini:
            # Rule result is sufficiently confident — use it directly
            logger.info(
                "CorrelationAgent: Rule confidence %.2f >= %.2f — skipping Gemini.",
                rule_output.confidence_score,
                _RULE_CONFIDENCE_THRESHOLD,
            )
            final_output = rule_output

        else:
            # ── Step 4a: Retrieve historical incidents from ChromaDB ───
            rag_context = self._fetch_rag_context(updated_state, rule_output)

            # ── Step 4b: Call Gemini ───────────────────────────────────
            logger.info("CorrelationAgent: Calling GeminiCorrelationService...")
            gemini_output: CorrelationOutput = self._gemini_service.correlate(
                state=updated_state,
                rag_context=rag_context,
                existing_events=rule_output.correlated_events,
            )
            logger.info(
                "CorrelationAgent: Gemini → incident=%s confidence=%.2f",
                gemini_output.incident_type.value,
                gemini_output.confidence_score,
            )

            # ── Step 4c: Merge — prefer higher confidence ──────────────
            final_output = self._merge_outputs(rule_output, gemini_output, rag_context)

        elapsed_ms = int((time.perf_counter() - start_t) * 1000)
        logger.info(
            "CorrelationAgent: Completed in %dms — incident=%s confidence=%.2f source=%s",
            elapsed_ms,
            final_output.incident_type.value,
            final_output.confidence_score,
            final_output.source.value,
        )

        # ── Step 5: Write back to state ────────────────────────────────
        return updated_state.model_copy(
            update={"correlation_output": final_output}
        )

    def validate(self, state: CPUState) -> bool:
        """Validate that correlation_output is populated."""
        return (
            state.correlation_output is not None
            and state.correlation_output.incident_type is not None
        )

    # ─────────────────────────────────────────────────────────────────────
    # Signal population
    # ─────────────────────────────────────────────────────────────────────

    def _populate_signal_fields(self, state: CPUState) -> CPUState:
        """
        Derive free-text signal summaries from CPUState and write them
        into the six signal analysis fields.

        Fields that are already non-empty (set by a dedicated metric agent
        in a future phase) are left unchanged — this method only fills
        in defaults derived from the current metric data.
        """
        m = state.metrics
        updates: dict = {}

        # CPU analysis — always derived from metrics
        updates["cpu_analysis"] = (
            f"CPU usage: {m.cpu_usage:.1f}% | "
            f"Limit: {m.cpu_limit:.0f} | "
            f"Request: {m.cpu_request:.0f} | "
            f"Throttling: {m.throttling_percentage:.1f}% | "
            f"Trend: {m.cpu_trend.value} | "
            f"Avg 5m: {m.avg_cpu_last_5m:.1f}% | "
            f"Avg 15m: {m.avg_cpu_last_15m:.1f}%"
        )

        # Restart-based event_analysis scaffold
        if not state.event_analysis and m.restart_count > 0:
            updates["event_analysis"] = (
                f"Pod restart count: {m.restart_count}. "
                + ("CrashLoopBackOff suspected." if m.restart_count >= 5 else "")
            )

        # Memory / Disk / Network / Log — leave existing values; set placeholder if empty
        if not state.memory_analysis:
            updates["memory_analysis"] = "No memory signal available (dedicated agent not yet active)."
        if not state.disk_analysis:
            updates["disk_analysis"] = "No disk signal available (dedicated agent not yet active)."
        if not state.network_analysis:
            updates["network_analysis"] = "No network signal available (dedicated agent not yet active)."
        if not state.log_analysis:
            updates["log_analysis"] = "No log signal available (dedicated agent not yet active)."

        return state.model_copy(update=updates)

    # ─────────────────────────────────────────────────────────────────────
    # RAG retrieval
    # ─────────────────────────────────────────────────────────────────────

    def _fetch_rag_context(
        self, state: CPUState, rule_output: CorrelationOutput
    ) -> str:
        """
        Query ChromaDB for similar historical incidents to enrich the
        Gemini prompt and potentially boost confidence.

        Returns an empty string if retrieval fails (non-fatal).
        """
        try:
            signature = (
                f"Incident: {rule_output.incident_type.value}. "
                f"CPU: {state.metrics.cpu_usage:.1f}%. "
                f"Restarts: {state.metrics.restart_count}. "
                f"Signals: {state.cpu_analysis}"
            )
            severity_str = (
                state.analyzer_output.severity.value
                if state.analyzer_output and state.analyzer_output.severity
                else None
            )
            incidents = self._retriever.retrieve_similar_incidents(
                incident_signature=signature,
                severity=severity_str,
                root_cause=rule_output.incident_type.value
                if rule_output.incident_type != IncidentType.UNKNOWN
                else None,
            )
            runbooks = self._retriever.retrieve_runbooks(
                root_cause=rule_output.incident_type.value
            )
            rag_context = self._ctx_builder.build_rag_context(incidents, runbooks, [])
            logger.info(
                "CorrelationAgent: RAG retrieved %d incidents, %d runbooks.",
                len(incidents),
                len(runbooks),
            )
            return rag_context
        except Exception as exc:
            logger.warning("CorrelationAgent: RAG retrieval failed (non-fatal): %s", exc)
            return ""

    # ─────────────────────────────────────────────────────────────────────
    # Output merging
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _merge_outputs(
        rule_output: CorrelationOutput,
        gemini_output: CorrelationOutput,
        rag_context: str,
    ) -> CorrelationOutput:
        """
        Merge rule-based and Gemini outputs.

        Strategy:
          - Prefer the output with higher confidence_score.
          - If both are non-UNKNOWN and agree on incident_type, boost
            confidence by 5% (capped at 1.0) and mark source=HYBRID.
          - Correlated events from the rule engine are always preserved.
          - RAG historical context is preserved in the final output.
        """
        historical_match = bool(rag_context and rag_context.strip())

        # Both valid — pick higher confidence
        if gemini_output.confidence_score >= rule_output.confidence_score:
            primary, secondary = gemini_output, rule_output
        else:
            primary, secondary = rule_output, gemini_output

        # Determine source label
        both_valid = (
            rule_output.incident_type != IncidentType.UNKNOWN
            and gemini_output.incident_type != IncidentType.UNKNOWN
        )
        source = CorrelationSource.HYBRID if both_valid else primary.source

        # Boost confidence if both agree
        confidence = primary.confidence_score
        if both_valid and rule_output.incident_type == gemini_output.incident_type:
            confidence = min(1.0, confidence + 0.05)
            logger.info(
                "CorrelationAgent: Rule and Gemini agree on '%s' — boosting confidence to %.2f.",
                primary.incident_type.value,
                confidence,
            )

        return primary.model_copy(
            update={
                "source": source,
                "confidence_score": round(confidence, 3),
                "correlated_events": (
                    rule_output.correlated_events or primary.correlated_events
                ),
                "historical_match": historical_match,
                "historical_context": rag_context if historical_match else None,
            }
        )
