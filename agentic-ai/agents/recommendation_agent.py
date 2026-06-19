"""
Recommendation Agent — Phase 10.
"""
import logging
from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.ai.gemini_recommendation_service import GeminiRecommendationService
from services.fallback_recommendation_service import FallbackRecommendationService
from schemas.recommendation_input import (
    RecommendationInputSchema, MetricsSnapshot, AnalyzerSummary, RootCauseSummary
)

logger = logging.getLogger(__name__)

class RecommendationAgent(BaseAgent):
    def __init__(self):
        self._gemini = GeminiRecommendationService()
        self._fallback = FallbackRecommendationService()

    @property
    def name(self) -> str:
        return "recommendation"

    def execute(self, state: CPUState) -> CPUState:
        # Build strict input schema
        m = state.metrics
        ao = state.analyzer_output
        rc = state.root_cause_output
        
        inp = RecommendationInputSchema(
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
            rag_context=state.knowledge_output.rag_context if state.knowledge_output else ""
        )

        try:
            output = self._gemini.recommend(inp)
        except Exception as e:
            logger.warning("RecommendationAgent fallback triggered: %s", str(e))
            output = self._fallback.generate_recommendations(
                metrics=state.metrics,
                analyzer_output=state.analyzer_output,
                root_cause_output=state.root_cause_output
            )
        return state.model_copy(update={"recommendation_output": output})
