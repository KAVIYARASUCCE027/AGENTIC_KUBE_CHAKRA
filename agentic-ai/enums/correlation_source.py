"""
CorrelationSource Enum — Phase 12.

Tracks which analysis path produced the final CorrelationOutput.
This is vital for observability: you can tell at a glance whether
the incident classification came from deterministic rules, Gemini AI,
or a hybrid of both.
"""
from enum import Enum


class CorrelationSource(str, Enum):
    """
    Identifies the origin of a CorrelationOutput.

    Values:
        RULE_BASED  — Deterministic JSON rules matched with high confidence.
        GEMINI      — Gemini AI produced the result (rule confidence too low).
        HYBRID      — Rule-based matched AND Gemini was consulted; results merged.
        FALLBACK    — All methods failed; safe default applied.
    """

    RULE_BASED  = "RULE_BASED"
    GEMINI      = "GEMINI"
    HYBRID      = "HYBRID"
    FALLBACK    = "FALLBACK"
