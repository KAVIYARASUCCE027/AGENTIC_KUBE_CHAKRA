"""
Test RAG consumption in Action Planner Agent.
"""
import pytest
from unittest.mock import patch, MagicMock
from agents.action_planner_agent import ActionPlannerAgent
from schemas.cpu_state import CPUState
from schemas.knowledge.knowledge_output import KnowledgeAgentOutput

class TestRagActionPlanner:
    @patch("agents.action_planner_agent.GeminiActionPlannerService")
    @patch("agents.action_planner_agent.FallbackActionPlannerService")
    def test_action_planner_agent_uses_rag_context(self, MockFallback, MockGemini):
        mock_gemini = MockGemini.return_value
        
        agent = ActionPlannerAgent()
        agent._gemini = mock_gemini
        
        # Build mock state
        from schemas.cpu_state import InputState
        state = CPUState(inputs=InputState(pod_name="test-pod", namespace="default"))
        state.knowledge_output = KnowledgeAgentOutput(
            rag_context="Historical runbook RUNBOOK-003 succeeded."
        )
        
        agent.execute(state)
        
        # Verify that the input schema passed to gemini has rag_context
        mock_gemini.plan_action.assert_called_once()
        inp = mock_gemini.plan_action.call_args[0][0]
        
        assert inp.rag_context == "Historical runbook RUNBOOK-003 succeeded."
