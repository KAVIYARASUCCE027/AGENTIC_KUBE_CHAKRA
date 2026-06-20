"""
Disk Agent — Phase 16.
"""
import logging
import json
from langchain_core.prompts import PromptTemplate

from services.llm_service import get_llm
from schemas.multi_resource_state import MultiResourceState
from schemas.disk_insight import DiskInsight, DiskMetrics
from schemas.base_insight import BaseInsightInputs, BaseInsightOutputs
from schemas.common import ResourceSeverity
from services.metrics.disk_service import DiskMetricService
from services.global_bus import publisher
from schemas.event_message import EventMessage
from memory.disk_history import DiskHistory
from prompts.disk_prompt import DISK_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

class DiskAgent:
    def __init__(self):
        self._llm = get_llm()
        self._metric_svc = DiskMetricService()
        self._history = DiskHistory()
        self._prompt = PromptTemplate.from_template(DISK_ANALYSIS_PROMPT)

    def execute(self, state: MultiResourceState) -> MultiResourceState:
        logger.info("Executing Disk Agent...")
        
        pod_name = state.cpu_state.inputs.pod_name
        namespace = state.cpu_state.inputs.namespace
        metrics_data = self._metric_svc.get_disk_metrics(pod_name, namespace)
        
        prompt_val = self._prompt.format(**metrics_data)
        response = self._llm.invoke(prompt_val)
        
        outputs = None
        try:
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

        insight = DiskInsight(
            inputs=BaseInsightInputs(pod_name=pod_name, namespace=namespace),
            metrics=DiskMetrics(**metrics_data),
            outputs=outputs
        )
        
        self._history.add_history(
            pod_name=pod_name, 
            severity=outputs.severity.value, 
            root_cause=outputs.root_cause, 
            recommendations=", ".join(outputs.recommendations)
        )
        
        state.disk_insight = insight

        # Phase 18: Publish event
        publisher.publish_sync(
            publisher.publish_disk_event(
                source_agent=self.__class__.__name__,
                severity=outputs.severity,
                payload={"analysis": outputs.analysis, "root_cause": outputs.root_cause}
            )
        )
        return state

    async def handle_event(self, event: EventMessage):
        """Async event handler for Event Bus interactions."""
        pass
