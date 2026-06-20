"""
Memory Node — Phase 16.
"""
from schemas.multi_resource_state import MultiResourceState
from agents.memory_agent import MemoryAgent

def memory_node(state: MultiResourceState) -> MultiResourceState:
    agent = MemoryAgent()
    return agent.execute(state)
