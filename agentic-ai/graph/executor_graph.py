"""
Executor Graph — Phase 15.
"""
from langgraph.graph import StateGraph, END

from schemas.execution_graph_state import ExecutionGraphState
from nodes.executor.executor_node import executor_node
from nodes.executor.verification_node import verification_node
from nodes.executor.audit_node import audit_node
from nodes.executor.memory_node import memory_node

def build_executor_graph() -> StateGraph:
    """
    Builds the execution sub-graph:
    START -> Executor Node -> Verification Node -> Audit Node -> Memory Node -> END
    """
    graph_builder = StateGraph(ExecutionGraphState)

    # Add nodes
    graph_builder.add_node("executor", executor_node)
    graph_builder.add_node("verification", verification_node)
    graph_builder.add_node("audit", audit_node)
    graph_builder.add_node("memory", memory_node)

    # Define edges
    graph_builder.set_entry_point("executor")
    graph_builder.add_edge("executor", "verification")
    graph_builder.add_edge("verification", "audit")
    graph_builder.add_edge("audit", "memory")
    graph_builder.add_edge("memory", END)

    return graph_builder.compile()

# Provide a pre-compiled instance for convenience
executor_graph = build_executor_graph()
