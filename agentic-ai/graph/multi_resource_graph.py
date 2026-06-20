"""
Multi-Resource Graph — Phase 16.
"""
from langgraph.graph import StateGraph, START, END

from schemas.multi_resource_state import MultiResourceState

# Import nodes
from nodes.memory_node import memory_node
from nodes.disk_node import disk_node
from nodes.network_node import network_node
from nodes.log_node import log_node
from nodes.event_node import event_node

def cpu_node(state: MultiResourceState) -> MultiResourceState:
    """
    Placeholder/Wrapper for the CPU Agent.
    In a full run, this could invoke the compiled CPU StateGraph.
    For now, it assumes state.cpu_state is already populated or delegates logic.
    """
    # Just pass through for Phase 16; CPU insights are already managed in cpu_state
    return state

def build_multi_resource_graph() -> StateGraph:
    """
    Builds the multi-agent execution graph:
    START -> CPU -> Memory -> Disk -> Network -> Log -> Event -> END
    """
    graph_builder = StateGraph(MultiResourceState)

    # Add nodes
    graph_builder.add_node("cpu_node", cpu_node)
    graph_builder.add_node("memory_node", memory_node)
    graph_builder.add_node("disk_node", disk_node)
    graph_builder.add_node("network_node", network_node)
    graph_builder.add_node("log_node", log_node)
    graph_builder.add_node("event_node", event_node)

    # Define edges (Sequential execution)
    graph_builder.add_edge(START, "cpu_node")
    graph_builder.add_edge("cpu_node", "memory_node")
    graph_builder.add_edge("memory_node", "disk_node")
    graph_builder.add_edge("disk_node", "network_node")
    graph_builder.add_edge("network_node", "log_node")
    graph_builder.add_edge("log_node", "event_node")
    graph_builder.add_edge("event_node", END)

    return graph_builder.compile()

# Provide a pre-compiled instance for convenience
multi_resource_graph = build_multi_resource_graph()
