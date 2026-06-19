"""
Test RAG consumption in Recommendation Agent.
"""
import pytest
from unittest.mock import patch, MagicMock
from agents.recommendation_agent import RecommendationAgent
from schemas.cpu_state import CPUState
from schemas.knowledge.knowledge_output import KnowledgeAgentOutput

class TestRagRecommendation:
    @patch("agents.recommendation_agent.GeminiRecommendationService")
    @patch("agents.recommendation_agent.FallbackRecommendationService")
    def test_recommendation_agent_uses_rag_context(self, MockFallback, MockGemini):
        mock_gemini = MockGemini.return_value
        
        agent = RecommendationAgent()
        agent._gemini = mock_gemini
        
        # Build mock state
        from schemas.cpu_state import InputState
        state = CPUState(inputs=InputState(pod_name="test-pod", namespace="default"))
        state.knowledge_output = KnowledgeAgentOutput(
            rag_context="Historical incident INC-023 with CPU_LIMIT_REACHED was resolved by enabling HPA."
        )
        
        agent.execute(state)
        
        # Verify that the input schema passed to gemini has rag_context
        mock_gemini.recommend.assert_called_once()
        inp = mock_gemini.recommend.call_args[0][0]
        
        assert inp.rag_context == "Historical incident INC-023 with CPU_LIMIT_REACHED was resolved by enabling HPA."
