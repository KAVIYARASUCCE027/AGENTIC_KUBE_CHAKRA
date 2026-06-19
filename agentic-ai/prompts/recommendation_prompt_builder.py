"""
Recommendation Prompt Builder — Phase 7.

Loads system prompt and user template from disk, injects live values
from RecommendationInputSchema, and returns the final prompts ready
for the Gemini service.

Keeping prompt construction separate from the Gemini call ensures the
service stays a thin HTTP wrapper and prompt logic is independently testable.
"""
from __future__ import annotations

import logging
from pathlib import Path

from schemas.recommendation_input import RecommendationInputSchema

logger = logging.getLogger(__name__)

_PROMPTS_DIR       = Path(__file__).resolve().parent
_SYSTEM_PROMPT_FILE = _PROMPTS_DIR / "recommendation_system_prompt.txt"
_TEMPLATE_FILE      = _PROMPTS_DIR / "recommendation_template.txt"


def _load_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def _format_list(items: list[str], indent: str = "  ") -> str:
    if not items:
        return f"{indent}- (none)"
    return "\n".join(f"{indent}- {item}" for item in items)


class RecommendationPromptBuilder:
    """
    Builds the (system_prompt, user_prompt) tuple for the Recommendation Agent.

    Usage:
        builder = RecommendationPromptBuilder()
        system, user = builder.build(input_schema)
    """

    def __init__(self) -> None:
        self._system_template = _load_file(_SYSTEM_PROMPT_FILE)
        self._user_template   = _load_file(_TEMPLATE_FILE)
        logger.debug("RecommendationPromptBuilder: Prompt files loaded.")

    def build(self, inp: RecommendationInputSchema) -> tuple[str, str]:
        """
        Inject runtime values into the user template.

        Args:
            inp: Validated input schema built from CPUState.

        Returns:
            (system_prompt, user_prompt) strings ready for Gemini.
        """
        m  = inp.metrics
        ao = inp.analyzer_output
        rc = inp.root_cause_output

        user_prompt = self._user_template.format(
            pod_name=inp.pod_name,
            namespace=inp.namespace,
            timestamp=inp.timestamp.isoformat(),
            cpu_usage=m.cpu_usage,
            avg_cpu_5m=m.avg_cpu_5m,
            avg_cpu_15m=m.avg_cpu_15m,
            cpu_trend=m.cpu_trend,
            throttling_percentage=m.throttling_percentage,
            cpu_limit=m.cpu_limit,
            cpu_request=m.cpu_request,
            restart_count=m.restart_count,
            replica_count=m.replica_count,
            health_status=ao.health_status.value,
            severity=ao.severity.value,
            abnormality=ao.abnormality.value,
            trend=ao.trend,
            analyzer_confidence=ao.confidence,
            analyzer_reasoning=_format_list(ao.reasoning),
            root_cause=rc.root_cause.value,
            root_cause_confidence=rc.confidence,
            root_cause_source=rc.source,
            root_cause_evidence=_format_list(rc.evidence),
            root_cause_reasoning=_format_list(rc.reasoning),
            rag_context=inp.rag_context if inp.rag_context else "NO RELEVANT HISTORICAL CONTEXT FOUND.",
        )

        logger.debug(
            "RecommendationPromptBuilder: User prompt built for %s/%s.",
            inp.namespace, inp.pod_name
        )
        return self._system_template, user_prompt
