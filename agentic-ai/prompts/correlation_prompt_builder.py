"""
Correlation Prompt Builder — Phase 12.

Loads the system prompt and user template from disk, injects live
signal values from CPUState, and returns the final prompts ready
for GeminiCorrelationService.

Keeping prompt construction separate from the Gemini call ensures the
service remains a thin HTTP wrapper, and the prompt logic is
independently testable.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPTS_DIR         = Path(__file__).resolve().parent
_SYSTEM_PROMPT_FILE  = _PROMPTS_DIR / "correlation_system_prompt.txt"
_TEMPLATE_FILE       = _PROMPTS_DIR / "correlation_template.txt"


def _load_file(path: Path) -> str:
    """Load and return the contents of a prompt file."""
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


class CorrelationPromptBuilder:
    """
    Builds the (system_prompt, user_prompt) tuple for the Correlation Agent.

    Usage:
        builder = CorrelationPromptBuilder()
        system, user = builder.build(
            pod_name="nginx-...",
            namespace="production",
            cpu_analysis="CPU at 92%, throttling 35%.",
            memory_analysis="Memory at 94%, OOMKilled event.",
            disk_analysis="Disk at 40%, healthy.",
            network_analysis="No anomalies detected.",
            log_analysis="No error patterns in logs.",
            event_analysis="OOMKilled event 3 times in last 10 minutes.",
            historical_context="Similar incident resolved by increasing memory limit.",
        )
    """

    def __init__(self) -> None:
        self._system_prompt = _load_file(_SYSTEM_PROMPT_FILE)
        self._user_template = _load_file(_TEMPLATE_FILE)
        logger.debug("CorrelationPromptBuilder: Prompt files loaded.")

    def build(
        self,
        pod_name: str,
        namespace: str,
        cpu_analysis: str,
        memory_analysis: str,
        disk_analysis: str,
        network_analysis: str,
        log_analysis: str,
        event_analysis: str,
        historical_context: str = "",
    ) -> tuple[str, str]:
        """
        Inject signal values into the user template.

        Args:
            pod_name:           Target pod name.
            namespace:          Target namespace.
            cpu_analysis:       CPU signal summary string.
            memory_analysis:    Memory signal summary string.
            disk_analysis:      Disk signal summary string.
            network_analysis:   Network signal summary string.
            log_analysis:       Log signal summary string.
            event_analysis:     Kubernetes Events signal summary string.
            historical_context: RAG context from ChromaDB (empty string if none).

        Returns:
            (system_prompt, user_prompt) strings ready for Gemini.
        """
        historical_section = (
            historical_context.strip()
            if historical_context.strip()
            else "No historical incidents retrieved."
        )

        user_prompt = self._user_template.format(
            pod_name=pod_name,
            namespace=namespace,
            cpu_analysis=cpu_analysis or "No CPU signal available.",
            memory_analysis=memory_analysis or "No memory signal available.",
            disk_analysis=disk_analysis or "No disk signal available.",
            network_analysis=network_analysis or "No network signal available.",
            log_analysis=log_analysis or "No log signal available.",
            event_analysis=event_analysis or "No Kubernetes events available.",
            historical_context=historical_section,
        )

        logger.debug(
            "CorrelationPromptBuilder: User prompt built for %s/%s.",
            namespace,
            pod_name,
        )
        return self._system_prompt, user_prompt
