"""
Execution Graph State Schema — Phase 15.
"""
from typing import TypedDict, Optional
from schemas.execution_input import ExecutionInput
from schemas.execution_result import ExecutionResult

class ExecutionGraphState(TypedDict):
    """
    Shared state for the Executor LangGraph workflow.
    """
    input: ExecutionInput
    backup_yaml: Optional[str]
    result: Optional[ExecutionResult]
    audit_id: Optional[str]
    history_id: Optional[str]
