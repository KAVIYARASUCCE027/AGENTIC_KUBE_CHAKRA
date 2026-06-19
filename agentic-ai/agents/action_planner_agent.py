"""
Action Planner Agent — Phase 10.
"""
import logging
from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.ai.gemini_action_planner_service import GeminiActionPlannerService
from services.fallback_action_planner_service import FallbackActionPlannerService
from schemas.action_plan_input import (
    ActionPlanInputSchema, MetricsSnapshot, AnalyzerSummary, RootCauseSummary, RecommendationSummary
)

logger = logging.getLogger(__name__)

class ActionPlannerAgent(BaseAgent):
    def __init__(self):
        self._gemini = GeminiActionPlannerService()
        self._fallback = FallbackActionPlannerService()

    @property
    def name(self) -> str:
        return "action_planner"

    def execute(self, state: CPUState) -> CPUState:
        m = state.metrics
        ao = state.analyzer_output
        rc = state.root_cause_output
        ro = state.recommendation_output
        
        inp = ActionPlanInputSchema(
            pod_name=state.inputs.pod_name,
            namespace=state.inputs.namespace,
            metrics=MetricsSnapshot(
                cpu_usage=m.cpu_usage,
                avg_cpu_5m=m.avg_cpu_last_5m,
                avg_cpu_15m=m.avg_cpu_last_15m,
                cpu_trend=m.cpu_trend.value,
                cpu_limit=m.cpu_limit,
                cpu_request=m.cpu_request,
                restart_count=m.restart_count,
                replica_count=m.replica_count,
            ),
            analyzer_output=AnalyzerSummary(
                health_status=ao.health_status,
                severity=ao.severity,
                abnormality=ao.abnormality,
                confidence=ao.confidence,
            ),
            root_cause_output=RootCauseSummary(
                root_cause=rc.root_cause,
                confidence=rc.confidence,
                evidence=list(rc.evidence),
                source=rc.source.value,
            ),
            recommendation_output=RecommendationSummary(
                recommendations=list(ro.recommendations),
                reasoning=list(ro.reasoning),
                confidence=ro.confidence,
            ),
            rag_context=state.knowledge_output.rag_context if state.knowledge_output else ""
        )

        try:
            output = self._gemini.plan_action(inp)
        except Exception as e:
            logger.warning("ActionPlannerAgent fallback triggered: %s", str(e))
            output = self._fallback.generate_action_plan(
                metrics=state.metrics,
                analyzer_output=state.analyzer_output,
                root_cause_output=state.root_cause_output,
                recommendation_output=state.recommendation_output
            )
        return state.model_copy(update={"action_plan_output": output})
