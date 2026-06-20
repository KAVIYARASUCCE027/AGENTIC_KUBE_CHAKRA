"""
Event Node — Phase 16.
"""
from schemas.multi_resource_state import MultiResourceState
from agents.k8s_event_agent import EventAgent

def event_node(state: MultiResourceState) -> MultiResourceState:
    agent = EventAgent()
    return agent.execute(state)
