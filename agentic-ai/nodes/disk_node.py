"""
Disk Node — Phase 16.
"""
from schemas.multi_resource_state import MultiResourceState
from agents.disk_agent import DiskAgent

def disk_node(state: MultiResourceState) -> MultiResourceState:
    agent = DiskAgent()
    return agent.execute(state)
