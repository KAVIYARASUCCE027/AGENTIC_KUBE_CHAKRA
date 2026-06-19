"""
CPU Agent Graph Module.
Defines the LangGraph pipeline for the CPU Analysis Agent.

Phase 12 pipeline:
    metric_collector → correlation → analyzer → root_cause
    → knowledge → recommendation → action_planner → memory
"""
import logging
from langgraph.graph import StateGraph, START, END

from schemas.cpu_state import CPUState
from nodes.cpu.metric_collector_node import metric_collector
from nodes.cpu.correlation_node import correlation_node
from nodes.cpu.analyzer_node import analyzer_node
from nodes.cpu.root_cause_node import root_cause_node
from nodes.cpu.knowledge_node import knowledge_node
from nodes.cpu.recommendation_node import recommendation_node
from nodes.cpu.action_planner_node import action_planner_node
from nodes.cpu.human_approval_node import human_approval_node
from nodes.cpu.executor_node import executor_node
from nodes.cpu.memory_node import memory_node

from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

# Module-level MemorySaver for check-pointing across API calls
memory_saver = MemorySaver()

def check_approval(state: CPUState) -> str:
    """Conditional routing based on approval status."""
    if not state.approval_output:
        return "PENDING"
    
    status = state.approval_output.approval_status
    if status == "APPROVED":
        return "APPROVED"
    elif status == "REJECTED":
        return "REJECTED"
    return "PENDING"

def build_cpu_graph() -> StateGraph:
    """
    Builds and compiles the CPU Analysis LangGraph.

    Phase 12 adds the correlation_node between metric_collector and
    analyzer, enriching the shared state with a multi-signal incident
    classification before downstream agents run.

    Returns:
        A compiled StateGraph ready for execution.
    """
    logger.info("Building CPU Agent LangGraph (Phase 12)...")

    # 1. Initialize StateGraph with CPUState
    graph_builder = StateGraph(CPUState)

    # 2. Add nodes
    graph_builder.add_node("metric_collector", metric_collector)
    graph_builder.add_node("correlation", correlation_node)       # Phase 12
    graph_builder.add_node("analyzer", analyzer_node)
    graph_builder.add_node("root_cause", root_cause_node)
    graph_builder.add_node("knowledge", knowledge_node)
    graph_builder.add_node("recommendation", recommendation_node)
    graph_builder.add_node("action_planner", action_planner_node)
    graph_builder.add_node("human_approval", human_approval_node) # Phase 14
    graph_builder.add_node("executor", executor_node)             # Phase 14
    graph_builder.add_node("memory", memory_node)

    # 3. Define the edges (workflow)
    graph_builder.add_edge(START, "metric_collector")
    graph_builder.add_edge("metric_collector", "correlation")     # Phase 12
    graph_builder.add_edge("correlation", "analyzer")             # Phase 12
    graph_builder.add_edge("analyzer", "root_cause")
    graph_builder.add_edge("root_cause", "knowledge")
    graph_builder.add_edge("knowledge", "recommendation")
    graph_builder.add_edge("recommendation", "action_planner")
    graph_builder.add_edge("action_planner", "human_approval")
    
    # Conditional edge from human_approval
    graph_builder.add_conditional_edges(
        "human_approval",
        check_approval,
        {
            "APPROVED": "executor",
            "REJECTED": "memory",
            "PENDING": END
        }
    )
    
    graph_builder.add_edge("executor", "memory")
    graph_builder.add_edge("memory", END)

    # 4. Compile graph with checkpointer
    compiled_graph = graph_builder.compile(checkpointer=memory_saver)
    logger.info("CPU Agent LangGraph (Phase 12) compiled successfully.")

    return compiled_graph

