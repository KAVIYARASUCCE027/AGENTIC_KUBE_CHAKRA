"""
CPU State Module — Phase 2.

Defines the shared CPUState that acts as the single source of truth for all
nodes in the LangGraph CPU analysis pipeline. Every node reads from and
updates this state.

Architecture:
    CPUState (root)
    ├── inputs    → InputState       — Kubernetes pod identification
    ├── metrics   → MetricState      — CPU utilisation & trend data
    ├── ai_output → AIOutputState    — LLM-generated analysis & recommendations
    ├── memory    → MemoryState      — Historical incident correlation
    └── metadata  → MetadataState    — Execution tracking & observability

Design Decisions:
    • Nested Pydantic models keep each concern isolated and independently
      testable while composing into a single coherent state object.
    • Enums enforce a closed set of valid values for severity and status,
      preventing typos and invalid states at the type level.
    • Every optional field carries a safe default so the state can be
      partially constructed at any point in the graph execution.
    • Field descriptions and examples power auto-generated API docs and
      make the schema self-documenting for future contributors.
    • The design is future-proof: new metrics or memory fields can be added
      to the relevant sub-model without touching the root CPUState.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas.analyzer_output import AnalyzerOutputState, Severity
from schemas.root_cause_output import RootCauseOutputState
from schemas.recommendation_output import RecommendationOutputState
from schemas.action_plan_output import ActionPlanOutputState
from schemas.memory_output import MemoryOutputState
from schemas.knowledge.knowledge_output import KnowledgeAgentOutput
from schemas.correlation.correlation_output import CorrelationOutput
from schemas.approval.approval_output import ApprovalOutputState
from schemas.approval.execution_output import ExecutionOutputState

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================



class ExecutionStatus(str, Enum):
    """
    Lifecycle status of a single agent execution run.

    Transitions: PENDING → RUNNING → COMPLETED | FAILED
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CPUTrend(str, Enum):
    """
    Directional trend of CPU utilisation over time.

    Used by the analysis node to contextualise raw metric snapshots.
    """

    INCREASING = "INCREASING"
    STABLE = "STABLE"
    DECREASING = "DECREASING"


# =============================================================================
# Sub-Models
# =============================================================================

class InputState(BaseModel):
    """
    Kubernetes pod identification inputs.

    Populated at the very start of the pipeline by the API handler or
    the orchestrating agent before the graph is invoked.
    """

    pod_name: str = Field(
        ...,
        min_length=1,
        max_length=253,
        description="Kubernetes pod name to analyse.",
        examples=["nginx-deployment-7c79c4bf97-x8j2k"],
    )
    namespace: str = Field(
        ...,
        min_length=1,
        max_length=253,
        description="Kubernetes namespace containing the target pod.",
        examples=["production"],
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp marking the start of analysis.",
        examples=["2026-06-17T04:00:00Z"],
    )
    cluster_name: str = Field(
        default="",
        max_length=253,
        description="Cluster identifier (e.g. GKE cluster name).",
        examples=["gke-prod-us-central1"],
    )
    node_name: str = Field(
        default="",
        max_length=253,
        description="Worker node where the pod is scheduled.",
        examples=["gke-prod-pool-1-abc12345-xyz0"],
    )

    class Config:
        json_schema_extra = {
            "title": "InputState",
            "description": "Kubernetes pod identification fields.",
        }


class MetricState(BaseModel):
    """
    CPU utilisation metrics collected from Prometheus / Kubernetes API.

    All numeric fields default to 0.0 / 0 so the state can be safely
    constructed before the collect node has executed.
    """

    # --- Current snapshot ---
    cpu_usage: float = Field(
        default=0.0,
        ge=0.0,
        description="Current CPU utilisation percentage.",
        examples=[72.5],
    )
    cpu_limit: float = Field(
        default=0.0,
        ge=0.0,
        description="CPU limit assigned to the pod (in millicores or percentage).",
        examples=[1000.0],
    )
    cpu_request: float = Field(
        default=0.0,
        ge=0.0,
        description="CPU request configured for the pod (in millicores or percentage).",
        examples=[500.0],
    )

    # --- Operational counters ---
    restart_count: int = Field(
        default=0,
        ge=0,
        description="Number of container restarts for this pod.",
        examples=[3],
    )
    replica_count: int = Field(
        default=0,
        ge=0,
        description="Current number of running replicas.",
        examples=[3],
    )

    # --- Throttling ---
    throttling_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of CPU cycles that were throttled.",
        examples=[12.5],
    )

    # --- Trend analysis ---
    cpu_trend: CPUTrend = Field(
        default=CPUTrend.STABLE,
        description="Directional trend of CPU usage: INCREASING, STABLE, or DECREASING.",
        examples=["STABLE"],
    )
    avg_cpu_last_5m: float = Field(
        default=0.0,
        ge=0.0,
        description="Average CPU utilisation over the last 5 minutes.",
        examples=[68.2],
    )
    avg_cpu_last_15m: float = Field(
        default=0.0,
        ge=0.0,
        description="Average CPU utilisation over the last 15 minutes.",
        examples=[65.0],
    )
    avg_cpu_last_1h: float = Field(
        default=0.0,
        ge=0.0,
        description="Average CPU utilisation over the last 1 hour.",
        examples=[60.1],
    )

    class Config:
        json_schema_extra = {
            "title": "MetricState",
            "description": "CPU metrics collected from the monitoring stack.",
        }




class MetadataState(BaseModel):
    """
    Execution metadata for observability and debugging.

    Tracks which nodes have been visited, the current execution status,
    and any error messages — making every run fully auditable.
    """

    agent_name: str = Field(
        default="CPU_AGENT",
        description="Canonical name of this agent.",
        examples=["CPU_AGENT"],
    )
    agent_version: str = Field(
        default="2.0.0",
        description="Semantic version of the agent.",
        examples=["2.0.0"],
    )
    execution_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique UUID for this execution run.",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING,
        description="Current lifecycle status of the execution.",
        examples=["PENDING"],
    )
    current_node: str = Field(
        default="",
        description="Name of the LangGraph node currently executing.",
        examples=["collect"],
    )
    visited_nodes: list[str] = Field(
        default_factory=list,
        description="Ordered list of nodes that have completed execution.",
        examples=[["collect", "analyze", "recommend"]],
    )
    error_message: str = Field(
        default="",
        description="Error description if status is FAILED; empty otherwise.",
        examples=[""],
    )

    class Config:
        json_schema_extra = {
            "title": "MetadataState",
            "description": "Execution tracking and observability metadata.",
        }


# =============================================================================
# Root State — Single Source of Truth
# =============================================================================

class CPUState(BaseModel):
    """
    Root state model for the CPU Analysis Agent.

    This is the **single source of truth** shared across every node in the
    LangGraph pipeline.  Each node reads the sections it needs and writes
    back its outputs — ensuring a clean, predictable data flow.

    Sections:
        inputs                 — What pod are we analysing?
        metrics                — What does Prometheus tell us?
        analyzer_output        — Deterministic rules-based health analysis.
        root_cause_output      — AI-powered root cause identification.
        recommendation_output  — AI-powered SRE recommendations.
        action_plan_output     — AI-powered executable action plan.
        memory_output          — Contextual historical incident matches (Phase 9).
        knowledge_output       — Knowledge-based retrieval context.
        correlation_output     — Multi-signal event correlation result (Phase 12).
        cpu_analysis           — Free-text CPU signal summary for the correlator.
        memory_analysis        — Memory signal summary for the correlator.
        disk_analysis          — Disk signal summary for the correlator.
        network_analysis       — Network signal summary for the correlator.
        log_analysis           — Application log signal summary for the correlator.
        event_analysis         — Kubernetes Events signal summary for the correlator.
        metadata               — How is this run going?

    Usage:
        >>> state = CPUState(
        ...     inputs=InputState(pod_name="nginx", namespace="default"),
        ... )
        >>> state.metadata.execution_id  # auto-generated UUID
        'a1b2c3d4-...'
        >>> state.metadata.status
        <ExecutionStatus.PENDING: 'PENDING'>
    """

    inputs: InputState = Field(
        ...,
        description="Kubernetes pod identification inputs.",
    )
    metrics: MetricState = Field(
        default_factory=MetricState,
        description="CPU utilisation metrics from the monitoring stack.",
    )

    memory_output: Optional[MemoryOutputState] = Field(
        default=None,
        description="Results from the memory/correlation agent.",
    )
    
    approval_output: Optional[ApprovalOutputState] = Field(
        default_factory=ApprovalOutputState,
        description="Results from the human approval agent.",
    )
    
    execution_output: Optional[ExecutionOutputState] = Field(
        default_factory=ExecutionOutputState,
        description="Results from the executor agent.",
    )

    analyzer_output: AnalyzerOutputState = Field(
        default_factory=AnalyzerOutputState,
        description="Deterministic analysis and recommendations.",
    )
    root_cause_output: RootCauseOutputState = Field(
        default_factory=RootCauseOutputState,
        description="AI-powered root cause identification (Phase 6).",
    )
    recommendation_output: RecommendationOutputState = Field(
        default_factory=RecommendationOutputState,
        description="AI-powered SRE recommendations (Phase 7).",
    )
    action_plan_output: ActionPlanOutputState = Field(
        default_factory=ActionPlanOutputState,
        description="AI-powered executable action plan (Phase 8).",
    )
    memory_output: MemoryOutputState = Field(
        default_factory=MemoryOutputState,
        description="Historical incident memory for pattern correlation.",
    )
    knowledge_output: KnowledgeAgentOutput = Field(
        default_factory=KnowledgeAgentOutput,
        description="Knowledge-based retrieval context.",
    )
    # ---------------------------------------------------------------
    # Phase 12 — Event Correlation Engine fields
    # ---------------------------------------------------------------
    correlation_output: CorrelationOutput = Field(
        default_factory=CorrelationOutput,
        description="Multi-signal event correlation result (Phase 12).",
    )
    cpu_analysis: str = Field(
        default="",
        description="Free-text CPU signal summary passed to the Correlation Engine.",
    )
    memory_analysis: str = Field(
        default="",
        description="Memory signal summary passed to the Correlation Engine.",
    )
    disk_analysis: str = Field(
        default="",
        description="Disk signal summary passed to the Correlation Engine.",
    )
    network_analysis: str = Field(
        default="",
        description="Network signal summary passed to the Correlation Engine.",
    )
    log_analysis: str = Field(
        default="",
        description="Application log signal summary passed to the Correlation Engine.",
    )
    event_analysis: str = Field(
        default="",
        description="Kubernetes Events signal summary passed to the Correlation Engine.",
    )
    metadata: MetadataState = Field(
        default_factory=MetadataState,
        description="Execution tracking and observability metadata.",
    )

    class Config:
        json_schema_extra = {
            "title": "CPUState",
            "description": (
                "Shared state for the CPU analysis LangGraph pipeline. "
                "Every node reads from and writes to this model."
            ),
        }

    # -----------------------------------------------------------------
    # Convenience helpers
    # -----------------------------------------------------------------

    def mark_running(self, node_name: str) -> CPUState:
        """
        Transition the execution to RUNNING and record the current node.

        Args:
            node_name: The name of the node that is starting execution.

        Returns:
            A new CPUState instance with updated metadata.
        """
        return self.model_copy(
            update={
                "metadata": self.metadata.model_copy(
                    update={
                        "status": ExecutionStatus.RUNNING,
                        "current_node": node_name,
                    }
                )
            }
        )

    def mark_node_completed(self, node_name: str) -> CPUState:
        """
        Record that a node has finished execution.

        Appends the node name to `visited_nodes` and clears `current_node`.

        Args:
            node_name: The name of the node that completed.

        Returns:
            A new CPUState instance with updated metadata.
        """
        updated_visited = [*self.metadata.visited_nodes, node_name]
        return self.model_copy(
            update={
                "metadata": self.metadata.model_copy(
                    update={
                        "current_node": "",
                        "visited_nodes": updated_visited,
                    }
                )
            }
        )

    def mark_completed(self) -> CPUState:
        """
        Transition the execution to COMPLETED.

        Returns:
            A new CPUState instance with status set to COMPLETED.
        """
        return self.model_copy(
            update={
                "metadata": self.metadata.model_copy(
                    update={
                        "status": ExecutionStatus.COMPLETED,
                        "current_node": "",
                    }
                )
            }
        )

    def mark_failed(self, error: str) -> CPUState:
        """
        Transition the execution to FAILED and record the error message.

        Args:
            error: Human-readable error description.

        Returns:
            A new CPUState instance with status FAILED and error recorded.
        """
        return self.model_copy(
            update={
                "metadata": self.metadata.model_copy(
                    update={
                        "status": ExecutionStatus.FAILED,
                        "current_node": "",
                        "error_message": error,
                    }
                )
            }
        )

    def summary(self) -> str:
        """
        Return a compact human-readable summary of the current state.

        Useful for logging and debugging during graph execution.
        """
        return (
            f"[{self.metadata.agent_name} v{self.metadata.agent_version}] "
            f"exec={self.metadata.execution_id[:8]}… | "
            f"status={self.metadata.status.value} | "
            f"pod={self.inputs.namespace}/{self.inputs.pod_name} | "
            f"cpu={self.metrics.cpu_usage:.1f}% | "
            f"severity={self.analyzer_output.severity.value} | "
            f"nodes={self.metadata.visited_nodes}"
        )
