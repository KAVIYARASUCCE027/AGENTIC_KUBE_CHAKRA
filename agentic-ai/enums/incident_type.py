"""
IncidentType Enum — Phase 12.

Defines all higher-level incident classifications that the Event
Correlation Engine can identify by fusing multiple signals.

Using an enum prevents string literals from polluting downstream agents
and ensures the closed set of valid incident types is enforced at the
type level across the entire codebase.
"""
from enum import Enum


class IncidentType(str, Enum):
    """
    Higher-level incident classifications derived by correlating
    multiple signals (CPU, Memory, Disk, Network, Logs, K8s Events).
    """

    MEMORY_LEAK                  = "MEMORY_LEAK"
    APPLICATION_STARTUP_FAILURE  = "APPLICATION_STARTUP_FAILURE"
    STORAGE_EXHAUSTION           = "STORAGE_EXHAUSTION"
    NETWORK_MISCONFIGURATION     = "NETWORK_MISCONFIGURATION"
    NODE_RESOURCE_PRESSURE       = "NODE_RESOURCE_PRESSURE"
    CPU_THROTTLING               = "CPU_THROTTLING"
    CRASH_LOOP                   = "CRASH_LOOP"
    OOM_KILLED                   = "OOM_KILLED"
    UNKNOWN                      = "UNKNOWN"
