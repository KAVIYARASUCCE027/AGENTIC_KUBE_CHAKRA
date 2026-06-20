"""
Network Node — Phase 16.
"""
from schemas.multi_resource_state import MultiResourceState
from agents.network_agent import NetworkAgent

def network_node(state: MultiResourceState) -> MultiResourceState:
    agent = NetworkAgent()
    return agent.execute(state)
