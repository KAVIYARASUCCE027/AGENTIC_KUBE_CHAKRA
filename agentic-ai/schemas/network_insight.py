"""
Network Insight Schema — Phase 16.
"""
from schemas.base_insight import BaseInsight, BaseInsightMetrics
from pydantic import Field

class NetworkMetrics(BaseInsightMetrics):
    receive_bytes_total: str = Field(default="")
    transmit_bytes_total: str = Field(default="")
    connection_failures: int = Field(default=0)
    packet_loss_percentage: float = Field(default=0.0)

class NetworkInsight(BaseInsight):
    metrics: NetworkMetrics = Field(default_factory=NetworkMetrics)
