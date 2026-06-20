"""
Network Prompt — Phase 16.
"""

NETWORK_ANALYSIS_PROMPT = """
You are the Network Analysis Agent.
Analyze the following Kubernetes Network metrics to determine severity, root cause, and recommendations.

Metrics:
Usage: {usage}
Connection Failures: {connection_failures}
Packet Loss: {packet_loss_percentage}%
Trend: {trend}

Provide your analysis in JSON format matching the NetworkInsight schema:
{{
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "analysis": "string explanation",
  "root_cause": "string root cause (e.g., Congestion, DNS issue, External dependency failure)",
  "recommendations": ["Restart service", "Scale deployment", "Investigate ingress"]
}}
"""
