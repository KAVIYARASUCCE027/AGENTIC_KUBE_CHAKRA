"""
Event Correlation Service — Phase 12.

Implements deterministic, rule-based event correlation by loading
rules from `prompts/correlation_rules.json` and matching them against
the normalised signal flags derived from the current CPUState.

Design principles:
  - Rules are data, not code: adding a new rule requires no code change.
  - Signal detection is centralised in `_extract_signals()` — one place
    to update as new metric agents are added in future phases.
  - Returns a CorrelationOutput with source=RULE_BASED. When no rule
    matches, returns UNKNOWN with confidence=0.0 so the Gemini service
    can take over.
  - Completely stateless: safe to instantiate once and reuse across requests.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import List, Set

from schemas.cpu_state import CPUState
from schemas.correlation.correlated_event import CorrelatedEvent
from schemas.correlation.correlation_output import CorrelationOutput
from enums.incident_type import IncidentType
from enums.correlation_source import CorrelationSource

logger = logging.getLogger(__name__)

_RULES_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "correlation_rules.json"

# ─────────────────────────────────────────────────────────────────────────────
# Signal detection thresholds
# ─────────────────────────────────────────────────────────────────────────────
_CPU_HIGH_THRESHOLD         = 85.0   # %
_THROTTLING_HIGH_THRESHOLD  = 25.0   # %
_DISK_CRITICAL_THRESHOLD    = 95.0   # % (placeholder — disk not yet a metric)
_MEMORY_HIGH_THRESHOLD      = 85.0   # % (placeholder — memory not yet a metric)


class EventCorrelationService:
    """
    Rule-based Event Correlation Service.

    Evaluates a fixed set of JSON-driven correlation rules against the
    signals extracted from CPUState and returns the best-matching
    CorrelationOutput.

    Usage:
        service = EventCorrelationService()
        output  = service.correlate(state)
    """

    def __init__(self) -> None:
        self._rules: list[dict] = self._load_rules()
        logger.info(
            "EventCorrelationService: Loaded %d correlation rules from %s.",
            len(self._rules),
            _RULES_FILE,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────

    def correlate(self, state: CPUState) -> CorrelationOutput:
        """
        Evaluate all rules against the current CPUState.

        Returns the highest-confidence rule match as a CorrelationOutput.
        Falls back to UNKNOWN with confidence=0.0 if no rule matches.

        Args:
            state: The current shared CPUState.

        Returns:
            CorrelationOutput populated by the best-matching rule,
            or a safe UNKNOWN fallback.
        """
        start = time.monotonic()

        active_signals: Set[str] = self._extract_signals(state)
        correlated_events: List[CorrelatedEvent] = self._build_correlated_events(state)

        logger.info(
            "EventCorrelationService: Active signals — %s",
            sorted(active_signals),
        )

        best_rule: dict | None = None
        best_score: float = 0.0

        for rule in self._rules:
            required: Set[str] = set(rule["signals"])
            matched = required & active_signals
            if matched == required:
                # All required signals present — full match
                score: float = float(rule["confidence"])
                if score > best_score:
                    best_score = score
                    best_rule = rule
                    logger.info(
                        "EventCorrelationService: Rule '%s' matched with confidence %.2f.",
                        rule["name"],
                        score,
                    )
            elif matched:
                # Partial match — proportional confidence reduction
                partial_score = float(rule["confidence"]) * (len(matched) / len(required)) * 0.6
                if partial_score > best_score:
                    best_score = partial_score
                    best_rule = rule
                    logger.debug(
                        "EventCorrelationService: Rule '%s' partially matched (%.0f/%d signals) — score %.2f.",
                        rule["name"],
                        len(matched),
                        len(required),
                        partial_score,
                    )

        elapsed_ms = int((time.monotonic() - start) * 1000)

        if best_rule and best_score > 0.0:
            evidence = [
                best_rule.get("evidence_template", "").format(
                    cpu_usage=f"{state.metrics.cpu_usage:.1f}"
                )
            ]
            # Add relevant active signals as additional evidence
            for sig in active_signals:
                evidence.append(f"Signal detected: {sig}")

            return CorrelationOutput(
                incident_type=IncidentType(best_rule["incident_type"]),
                root_cause=best_rule["description"],
                confidence_score=round(best_score, 3),
                evidence=[e for e in evidence if e],
                correlation_summary=(
                    f"Rule '{best_rule['name']}' matched based on signals: "
                    f"{', '.join(sorted(set(best_rule['signals']) & active_signals))}. "
                    f"{best_rule['description']}"
                ),
                correlated_events=correlated_events,
                source=CorrelationSource.RULE_BASED,
                model_name="rule_engine",
                execution_time_ms=elapsed_ms,
                historical_match=False,
            )

        # No rule matched
        logger.info("EventCorrelationService: No rule matched. Returning UNKNOWN.")
        return CorrelationOutput(
            incident_type=IncidentType.UNKNOWN,
            root_cause="No deterministic rule matched the current signal combination.",
            confidence_score=0.0,
            evidence=[f"Active signals: {', '.join(sorted(active_signals)) or 'none'}"],
            correlation_summary="Signal combination did not match any known incident pattern.",
            correlated_events=correlated_events,
            source=CorrelationSource.RULE_BASED,
            model_name="rule_engine",
            execution_time_ms=elapsed_ms,
            historical_match=False,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Signal Extraction — single place to update as metric agents grow
    # ─────────────────────────────────────────────────────────────────────

    def _extract_signals(self, state: CPUState) -> Set[str]:
        """
        Derive a set of normalised signal flags from CPUState.

        Each flag corresponds to a signal keyword used in the rules JSON.
        As new metric agents are added (memory, disk, network, log,
        k8s_events), this method expands to include their signals.
        """
        signals: Set[str] = set()
        m = state.metrics

        # ── CPU signals ────────────────────────────────────────────────
        if m.cpu_usage >= _CPU_HIGH_THRESHOLD:
            signals.add("HIGH_CPU")

        if m.throttling_percentage >= _THROTTLING_HIGH_THRESHOLD:
            signals.add("HIGH_THROTTLING")

        # ── Memory signals (derived from free-text state fields) ───────
        mem = (state.memory_analysis or "").upper()
        if "HIGH_MEMORY" in mem or "MEMORY SPIKE" in mem or "MEMORY PRESSURE" in mem:
            signals.add("HIGH_MEMORY")
        if "MEMORY PRESSURE" in mem or "MEMORY_PRESSURE" in mem:
            signals.add("MEMORY_PRESSURE")
        if "OOMKILLED" in mem or "OOM KILL" in mem or "OOM_KILLED" in mem:
            signals.add("OOMKILLED")
        if "EVICTED" in mem:
            signals.add("EVICTED")

        # ── Disk signals ───────────────────────────────────────────────
        disk = (state.disk_analysis or "").upper()
        if "DISK_CRITICAL" in disk or "DISK CRITICAL" in disk or "DISK FULL" in disk:
            signals.add("DISK_CRITICAL")

        # ── Network signals ────────────────────────────────────────────
        net = (state.network_analysis or "").upper()
        if "NETWORK_TIMEOUT" in net or "NETWORK TIMEOUT" in net or "TIMEOUT" in net:
            signals.add("NETWORK_TIMEOUT")
        if "DNS_FAILURE" in net or "DNS FAILURE" in net or "DNS ERROR" in net:
            signals.add("DNS_FAILURE")

        # ── Log signals ────────────────────────────────────────────────
        logs = (state.log_analysis or "").upper()
        if "CRASHLOOPBACKOFF" in logs or "CRASH LOOP" in logs:
            signals.add("CRASHLOOPBACKOFF")
        if "READINESS_PROBE_FAILURE" in logs or "READINESS PROBE" in logs:
            signals.add("READINESS_PROBE_FAILURE")

        # ── Kubernetes Events signals ──────────────────────────────────
        events = (state.event_analysis or "").upper()
        if "OOMKILLED" in events or "OOM_KILLED" in events:
            signals.add("OOMKILLED")
        if "CRASHLOOPBACKOFF" in events or "CRASH LOOP" in events:
            signals.add("CRASHLOOPBACKOFF")
        if "EVICTED" in events:
            signals.add("EVICTED")
        if "READINESS" in events and "FAIL" in events:
            signals.add("READINESS_PROBE_FAILURE")
        if m.restart_count >= 3:
            signals.add("POD_RESTART")

        return signals

    def _build_correlated_events(self, state: CPUState) -> List[CorrelatedEvent]:
        """
        Build a structured list of CorrelatedEvent objects from CPUState.
        These are attached to every CorrelationOutput for observability.
        """
        events: List[CorrelatedEvent] = []
        m = state.metrics

        # CPU event
        cpu_severity = (
            "HIGH" if m.cpu_usage >= _CPU_HIGH_THRESHOLD
            else "MEDIUM" if m.cpu_usage >= 70.0
            else "LOW"
        )
        events.append(CorrelatedEvent(
            source="cpu",
            event=f"CPU usage at {m.cpu_usage:.1f}% | throttling: {m.throttling_percentage:.1f}%",
            severity=cpu_severity,
        ))

        # Restart event
        if m.restart_count > 0:
            events.append(CorrelatedEvent(
                source="k8s_events",
                event=f"Container restart count: {m.restart_count}",
                severity="HIGH" if m.restart_count >= 3 else "MEDIUM",
            ))

        # Memory event (from free-text field)
        if state.memory_analysis:
            events.append(CorrelatedEvent(
                source="memory",
                event=state.memory_analysis[:200],
                severity="HIGH" if "HIGH" in state.memory_analysis.upper() else "MEDIUM",
            ))

        # Disk event
        if state.disk_analysis:
            events.append(CorrelatedEvent(
                source="disk",
                event=state.disk_analysis[:200],
                severity="HIGH" if "CRITICAL" in state.disk_analysis.upper() else "LOW",
            ))

        # Network event
        if state.network_analysis:
            events.append(CorrelatedEvent(
                source="network",
                event=state.network_analysis[:200],
                severity="HIGH" if "TIMEOUT" in state.network_analysis.upper() else "LOW",
            ))

        # Log event
        if state.log_analysis:
            events.append(CorrelatedEvent(
                source="logs",
                event=state.log_analysis[:200],
                severity="HIGH" if "ERROR" in state.log_analysis.upper() else "INFO",
            ))

        # Kubernetes Events
        if state.event_analysis:
            events.append(CorrelatedEvent(
                source="k8s_events",
                event=state.event_analysis[:200],
                severity="HIGH" if any(
                    kw in state.event_analysis.upper()
                    for kw in ["OOMKILLED", "CRASHLOOP", "EVICTED"]
                ) else "MEDIUM",
            ))

        return events

    # ─────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _load_rules() -> list[dict]:
        """Load and parse the correlation rules JSON file."""
        if not _RULES_FILE.exists():
            logger.error(
                "EventCorrelationService: Rules file not found at %s.", _RULES_FILE
            )
            return []
        try:
            with _RULES_FILE.open(encoding="utf-8") as fh:
                rules = json.load(fh)
            logger.debug(
                "EventCorrelationService: Successfully parsed %d rules.", len(rules)
            )
            return rules
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(
                "EventCorrelationService: Failed to load rules: %s", exc
            )
            return []
