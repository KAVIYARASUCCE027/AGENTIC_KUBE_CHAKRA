"""
Correlation Node — Phase 12 (Thin Wrapper).

Delegates all logic to the CorrelationAgent via the MultiAgentCoordinator.
Follows the exact same thin-wrapper pattern used by all other CPU nodes.
"""
import logging
import time

from schemas.cpu_state import CPUState
from services.multi_agent_coordinator import MultiAgentCoordinator

logger = logging.getLogger(__name__)


def correlation_node(state: CPUState) -> CPUState:
    """
    LangGraph node that runs the Event Correlation Engine.

    Positioned between metric_collector and analyzer in the graph,
    this node enriches CPUState with a multi-signal incident
    classification before deterministic rules and AI agents run.

    Args:
        state: Incoming CPUState from metric_collector.

    Returns:
        Updated CPUState with correlation_output and signal fields set.
    """
    start_time = time.time()
    node_name = "correlation"

    state = state.mark_running(node_name)
    logger.info(
        "[%s] Node started: %s", state.metadata.execution_id, node_name
    )

    coordinator = MultiAgentCoordinator()
    new_state = coordinator.execute_agent(node_name, state)

    final_state = new_state.mark_node_completed(node_name)

    elapsed = time.time() - start_time
    logger.info(
        "[%s] %s_node completed in %.2fs — incident=%s confidence=%.2f",
        final_state.metadata.execution_id,
        node_name,
        elapsed,
        final_state.correlation_output.incident_type.value,
        final_state.correlation_output.confidence_score,
    )

    return final_state
