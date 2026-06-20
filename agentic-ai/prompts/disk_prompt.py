"""
Disk Prompt — Phase 16.
"""

DISK_ANALYSIS_PROMPT = """
You are the Disk Analysis Agent.
Analyze the following Kubernetes Disk metrics to determine severity, root cause, and recommendations.

Metrics:
Usage: {usage}
Limit: {limit}
Ephemeral Storage: {ephemeral_storage_usage}
Disk IO Read: {disk_io_read}
Disk IO Write: {disk_io_write}
Trend: {trend}

Provide your analysis in JSON format matching the DiskInsight schema:
{{
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "analysis": "string explanation",
  "root_cause": "string root cause (e.g., Full volume, Excessive logs, Temporary files)",
  "recommendations": ["Rotate logs", "Cleanup files", "Increase PVC size"]
}}
"""
