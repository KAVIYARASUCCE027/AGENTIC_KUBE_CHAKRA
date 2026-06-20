"""
Log Node — Phase 16.
"""
from schemas.multi_resource_state import MultiResourceState
from agents.log_agent import LogAgent

def log_node(state: MultiResourceState) -> MultiResourceState:
    agent = LogAgent()
    return agent.execute(state)
