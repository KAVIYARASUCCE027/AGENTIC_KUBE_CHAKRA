"""
Analyzer Agent — Phase 10.
"""
from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.analyzer_service import AnalyzerService
from services.global_bus import publisher
from schemas.event_message import EventMessage

class AnalyzerAgent(BaseAgent):
    def __init__(self):
        self._service = AnalyzerService()

    @property
    def name(self) -> str:
        return "analyzer"

    def execute(self, state: CPUState) -> CPUState:
        # Pass required inputs to the Analyzer Service
        output = self._service.analyze(
            cpu_usage_percent=state.metrics.cpu_usage,
            cpu_limit=state.metrics.cpu_limit,
            cpu_request=state.metrics.cpu_request,
            restart_count=state.metrics.restart_count,
            replica_count=state.metrics.replica_count,
            cpu_usage_5m_avg=state.metrics.avg_cpu_last_5m,
            cpu_usage_15m_avg=state.metrics.avg_cpu_last_15m,
        )
        # Phase 18: Publish event based on analysis severity
        publisher.publish_sync(
            publisher.publish_cpu_event(
                source_agent=self.name,
                severity=output.severity,
                payload={"analysis": output.analysis, "root_cause": output.root_cause}
            )
        )
        return state.model_copy(update={"analyzer_output": output})

    async def handle_event(self, event: EventMessage):
        """Async event handler for Event Bus interactions."""
        # For now, just logging the received event. CPU Agent mainly produces.
        pass
