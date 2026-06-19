"""
CorrelationOutput Schema — Phase 12.

The structured, validated output produced by the Correlation Agent.
Populated by either the rule-based EventCorrelationService, the
GeminiCorrelationService, or a hybrid of both.

Downstream agents (Root Cause, Recommendation, Action Planner) can
read this model from CPUState.correlation_output to enrich their
analysis with the multi-signal incident classification.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from enums.incident_type import IncidentType
from enums.correlation_source import CorrelationSource
from schemas.correlation.correlated_event import CorrelatedEvent


class CorrelationOutput(BaseModel):
    """
    Structured output from the Event Correlation Engine.

    Fields:
        incident_type       — The most probable high-level incident classification.
        root_cause          — Human-readable root cause description.
        confidence_score    — Confidence in the classification (0.0 – 1.0).
        evidence            — Supporting signals that drove this conclusion.
        correlation_summary — One-paragraph narrative combining all signals.
        correlated_events   — Individual events from each monitoring source.
        source              — Which analysis path produced this (RULE_BASED / GEMINI / HYBRID).
        model_name          — Gemini model used, or "rule_engine" for rule-based.
        execution_time_ms   — Total wall-clock time for correlation (ms).
        historical_match    — True if ChromaDB returned a matching past incident.
        historical_context  — RAG context snippet from ChromaDB (if matched).
        timestamp           — UTC timestamp of when correlation ran.
    """

    incident_type: IncidentType = Field(
        default=IncidentType.UNKNOWN,
        description="Most probable high-level incident classification.",
        examples=["MEMORY_LEAK"],
    )
    root_cause: str = Field(
        default="",
        description="Human-readable root cause description.",
        examples=["Unbounded memory growth in the application heap."],
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the incident classification (0.0 – 1.0).",
        examples=[0.95],
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Supporting signals that drove this conclusion.",
        examples=[["CPU at 92%", "Memory at 94%", "OOMKilled event detected"]],
    )
    correlation_summary: str = Field(
        default="",
        description="One-paragraph narrative summarising the correlated signals.",
        examples=["High CPU and memory usage combined with OOMKilled events..."],
    )
    correlated_events: List[CorrelatedEvent] = Field(
        default_factory=list,
        description="Individual events from each monitoring source.",
    )
    source: CorrelationSource = Field(
        default=CorrelationSource.FALLBACK,
        description="Which analysis path produced this output.",
        examples=["HYBRID"],
    )
    model_name: str = Field(
        default="rule_engine",
        description="Model or engine that produced this output.",
        examples=["gemini-2.5-flash"],
    )
    execution_time_ms: int = Field(
        default=0,
        ge=0,
        description="Total wall-clock time for correlation in milliseconds.",
        examples=[320],
    )
    historical_match: bool = Field(
        default=False,
        description="True when ChromaDB returned a similar past incident.",
        examples=[True],
    )
    historical_context: Optional[str] = Field(
        default=None,
        description="RAG context snippet from ChromaDB (if a historical match was found).",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when correlation analysis ran.",
    )

    class Config:
        json_schema_extra = {
            "title": "CorrelationOutput",
            "description": (
                "Validated output from the Event Correlation Engine. "
                "Combines rule-based and AI-powered multi-signal analysis."
            ),
        }
