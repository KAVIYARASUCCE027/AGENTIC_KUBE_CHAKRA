"""
Event Priority - Phase 18
"""
from enum import IntEnum

class EventPriority(IntEnum):
    """
    Priority ordering for events. Lower number = higher priority.
    """
    P1 = 1  # Critical: OOM_KILLED, CRASH_LOOP_BACKOFF, NODE_FAILURE
    P2 = 2  # High: CPU_CRITICAL, MEMORY_CRITICAL, NETWORK_CRITICAL
    P3 = 3  # Medium: WARNING events
    P4 = 4  # Informational
