"""
Schemas package for K8S Agentic AI Service.

Contains Pydantic models for request/response validation and
the shared CPUState used by all LangGraph nodes.

Exports:
    Phase 1 — API Models:
        CPURequest, CPUResponse

    Phase 2 — Agent State Models:
        SeverityLevel, ExecutionStatus, CPUTrend      (Enums)
        InputState, MetricState, AIOutputState         (Sub-models)
        IncidentRecord, MemoryState, MetadataState     (Sub-models)
        CPUState                                       (Root state)
"""

# Phase 1 — API request / response models
from schemas.cpu_schema import CPURequest, CPUResponse

# Phase 2 — Shared agent state
from schemas.cpu_state import (
    # Enums
    ExecutionStatus,
    CPUTrend,
    # Sub-models
    InputState,
    MetricState,
    MetadataState,
    # Root state
    CPUState,
)

from schemas.analyzer_output import AnalyzerOutputState, Severity, HealthStatus, AbnormalityType
from schemas.action_plan_input import ActionPlanInputSchema
from schemas.action_plan_output import ActionPlanOutputState
from schemas.memory_output import MemoryOutputState
from schemas.memory.incident_record import IncidentRecord

from schemas.coordinator import (
    AgentStatus,
    AgentExecutionState,
    ExecutionPolicy,
    CoordinatorInput,
    CoordinatorOutput,
)

from schemas.knowledge.chroma_schemas import (
    ChromaIncident,
    ChromaRunbook,
    KnowledgeDocument,
)
from schemas.knowledge.knowledge_output import KnowledgeAgentOutput

__all__ = [
    # Phase 1
    "CPURequest",
    "CPUResponse",
    # Phase 2 — Enums
    "Severity",
    "HealthStatus",
    "AbnormalityType",
    "ExecutionStatus",
    "CPUTrend",
    # Phase 2 — Sub-models
    "InputState",
    "MetricState",
    "AnalyzerOutputState",
    "ActionPlanInputSchema",
    "ActionPlanOutputState",
    "MemoryOutputState",
    "IncidentRecord",
    "MetadataState",
    
    # Phase 10 - Coordinator
    "AgentStatus",
    "AgentExecutionState",
    "ExecutionPolicy",
    "CoordinatorInput",
    "CoordinatorOutput",

    # Phase 11 - Knowledge / RAG
    "ChromaIncident",
    "ChromaRunbook",
    "KnowledgeDocument",
    "KnowledgeAgentOutput",

    # Phase 2 — Root
    "CPUState",
]
