"""
CPU Agent Module.

Provides the high-level CPU analysis agent that orchestrates the
LangGraph pipeline and returns structured results.
"""

import logging
from typing import Any

from graph.cpu_graph import build_cpu_graph
from memory.conversation_memory import save_message
import uuid

logger = logging.getLogger(__name__)


def run_cpu_agent(namespace: str, pod_name: str) -> dict[str, Any]:
    """
    Execute the CPU analysis agent pipeline.

    Orchestrates the full CPU analysis workflow:
        1. Collect CPU metrics from Prometheus
        2. Analyze metrics using Gemini LLM
        3. Generate actionable recommendations

    Saves the interaction to conversation memory for future reference.

    Args:
        namespace: The Kubernetes namespace of the target pod.
        pod_name: The name of the target pod.

    Returns:
        A dictionary containing:
            - status: 'success' or 'error'
            - message: The combined analysis and recommendation result,
                       or an error description.

    Raises:
        No exceptions are raised; all errors are caught and returned
        in the response dictionary.
    """
    logger.info(
        "CPU Agent: Starting analysis for pod '%s' in namespace '%s'.",
        pod_name,
        namespace,
    )

    try:
        # Build the LangGraph pipeline
        cpu_graph = build_cpu_graph()

        # Prepare initial state
        initial_state: dict[str, Any] = {
            "inputs": {
                "namespace": namespace,
                "pod_name": pod_name,
            }
        }

        # Execute the graph with a thread_id for persistence
        logger.info("CPU Agent: Executing graph pipeline...")
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        result: dict[str, Any] = cpu_graph.invoke(initial_state, config=config)

        # Extract results properly from state
        analyzer_out = result.get("analyzer_output")
        recommendation_out = result.get("recommendation_output")
        approval_out = result.get("approval_output")
        
        analysis: str = getattr(analyzer_out, "analysis", "No analysis available.")
        
        recs = getattr(recommendation_out, "recommendations", [])
        recommendation: str = ", ".join([r.value if hasattr(r, "value") else str(r) for r in recs]) if recs else "No recommendation available."
        
        approval_id = getattr(approval_out, "approval_id", None)

        # Combine output
        combined_output: str = (
            f"## CPU Analysis\n\n{analysis}\n\n"
            f"---\n\n"
            f"## Recommendations\n\n{recommendation}"
        )
        
        if approval_id:
            combined_output += f"\n\n---\n\n## Action Plan\n\nApproval Required. ID: `{approval_id}`\nThread ID: `{thread_id}`"

        # Save to conversation memory
        save_message(
            role="user",
            content=f"Analyze CPU for pod '{pod_name}' in namespace '{namespace}'.",
        )
        save_message(role="assistant", content=combined_output)

        logger.info("CPU Agent: Analysis completed successfully.")

        return {
            "status": "success",
            "message": combined_output,
            "approval_id": approval_id,
            "thread_id": thread_id,
        }

    except Exception as exc:
        error_msg: str = f"CPU Agent failed: {exc}"
        logger.error(error_msg, exc_info=True)

        return {
            "status": "error",
            "message": error_msg,
        }
