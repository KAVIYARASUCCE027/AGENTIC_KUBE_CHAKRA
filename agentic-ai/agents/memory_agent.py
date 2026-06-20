"""
Memory Agent — Phase 16.
"""
import logging
import json
from langchain_core.prompts import PromptTemplate
from pydantic import ValidationError

from services.llm_service import get_llm
from schemas.multi_resource_state import MultiResourceState
from schemas.memory_insight import MemoryInsight, MemoryMetrics
from schemas.base_insight import BaseInsightInputs, BaseInsightOutputs
from schemas.common import ResourceSeverity
from services.metrics.memory_service import MemoryMetricService
from services.global_bus import publisher
from schemas.event_message import EventMessage
from memory.memory_history import MemoryHistory
from prompts.memory_prompt import MEMORY_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

class MemoryAgent:
    def __init__(self):
        self._llm = get_llm()
        self._metric_svc = MemoryMetricService()
        self._history = MemoryHistory()
        self._prompt = PromptTemplate.from_template(MEMORY_ANALYSIS_PROMPT)

    def execute(self, state: MultiResourceState) -> MultiResourceState:
        logger.info("Executing Memory Agent...")
        
        # 1. Fetch Metrics
        pod_name = state.cpu_state.inputs.pod_name
        namespace = state.cpu_state.inputs.namespace
        metrics_data = self._metric_svc.get_memory_metrics(pod_name, namespace)
        
        # 2. Invoke LLM
        prompt_val = self._prompt.format(**metrics_data)
        response = self._llm.invoke(prompt_val)
        
        # 3. Parse output
        outputs = None
        try:
            # Simple cleanup for json code blocks
            clean_json = response.content.strip().replace("```json", "").replace("```", "")
            parsed = json.loads(clean_json)
            outputs = BaseInsightOutputs(
                severity=ResourceSeverity(parsed.get("severity", "LOW")),
                analysis=parsed.get("analysis", ""),
                root_cause=parsed.get("root_cause", ""),
                recommendations=parsed.get("recommendations", [])
            )
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            outputs = BaseInsightOutputs(severity=ResourceSeverity.LOW, analysis="Parse error")

        # 4. Construct Insight
        insight = MemoryInsight(
            inputs=BaseInsightInputs(pod_name=pod_name, namespace=namespace),
            metrics=MemoryMetrics(**metrics_data),
            outputs=outputs
        )
        
        # 5. Save Memory
        self._history.add_history(
            pod_name=pod_name, 
            severity=outputs.severity.value, 
            root_cause=outputs.root_cause, 
            recommendations=", ".join(outputs.recommendations)
        )
        
        state.memory_insight = insight

        # Phase 18: Publish event
        publisher.publish_sync(
            publisher.publish_memory_event(
                source_agent=self.__class__.__name__,
                severity=outputs.severity,
                payload={"analysis": outputs.analysis, "root_cause": outputs.root_cause}
            )
        )
        return state

    async def handle_event(self, event: EventMessage):
        """Async event handler for Event Bus interactions."""
        pass
