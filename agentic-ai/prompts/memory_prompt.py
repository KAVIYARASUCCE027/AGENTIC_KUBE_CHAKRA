"""
Memory Prompt — Phase 16.
"""

MEMORY_ANALYSIS_PROMPT = """
You are the Memory Analysis Agent.
Analyze the following Kubernetes Memory metrics to determine severity, root cause, and recommendations.

Metrics:
Usage: {usage}
Limit: {limit}
Request: {request}
OOM Killed Count: {oom_killed_count}
Restart Count: {restart_count}
Trend: {trend}

Provide your analysis in JSON format matching the MemoryInsight schema:
{{
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "analysis": "string explanation",
  "root_cause": "string root cause (e.g., Memory leak, High traffic, Under-provisioned container)",
  "recommendations": ["Scale replicas", "Increase memory limits"]
}}
"""
