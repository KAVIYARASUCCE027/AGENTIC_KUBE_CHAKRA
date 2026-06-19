"""
CorrelatedEvent Schema — Phase 12.

Represents a single correlated signal from one monitoring source
(CPU, Memory, Disk, Network, Logs, or Kubernetes Events).

A list of CorrelatedEvents is attached to every CorrelationOutput,
giving downstream agents and the API consumer full visibility into
which signals drove the incident classification.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class CorrelatedEvent(BaseModel):
    """
    A single correlated signal from one infrastructure monitoring source.

    Fields:
        source    — The monitoring domain that produced this signal.
        event     — Human-readable description of what was observed.
        severity  — Signal severity: HIGH, MEDIUM, LOW, or INFO.
    """

    source: str = Field(
        ...,
        description=(
            "Monitoring source domain. "
            "One of: cpu, memory, disk, network, logs, k8s_events."
        ),
        examples=["memory"],
    )
    event: str = Field(
        ...,
        description="Human-readable description of the observed signal.",
        examples=["Memory usage at 94% — above critical threshold."],
    )
    severity: Literal["HIGH", "MEDIUM", "LOW", "INFO"] = Field(
        default="MEDIUM",
        description="Severity of this individual signal.",
        examples=["HIGH"],
    )

    class Config:
        json_schema_extra = {
            "title": "CorrelatedEvent",
            "description": "A single correlated signal from one monitoring source.",
        }
