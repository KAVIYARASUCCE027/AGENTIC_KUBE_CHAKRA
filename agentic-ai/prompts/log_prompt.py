"""
Log Prompt — Phase 16.
"""

LOG_ANALYSIS_PROMPT = """
You are the Log Analysis Agent.
Analyze the following application log metrics to determine severity, root cause, and recommendations.

Metrics:
Error Count: {error_count}
Warn Count: {warn_count}
Fatal Count: {fatal_count}
CrashLoop Detected: {crashloop_detected}
Trend: {trend}

Provide your analysis in JSON format matching the LogInsight schema:
{{
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "analysis": "string explanation",
  "root_cause": "string root cause (e.g., Database failure, Timeout, Missing configuration, Application crash)",
  "recommendations": ["Restart pod", "Rollback deployment", "Increase timeout"]
}}
"""
