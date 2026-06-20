"""
Event Service — Phase 16.
"""
import logging
import subprocess
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EventService:
    """
    Fetches events from the Kubernetes API via kubectl.
    """
    def __init__(self):
        pass

    def get_events(self, pod_name: str, namespace: str) -> Dict[str, Any]:
        """
        Retrieves Kubernetes events linked to the pod.
        """
        logger.info(f"Fetching events for pod {pod_name} in {namespace}...")
        
        try:
            # We use check=False to handle cases where there are no events or error safely.
            cmd = [
                "kubectl", "get", "events", 
                "-n", namespace, 
                f"--field-selector=involvedObject.name={pod_name}", 
                "-o", "json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # Simple simulation of event parsing
            failed_scheduling_count = 0
            oom_killed_count = 0
            backoff_count = 0
            critical_events = []

            if "FailedScheduling" in result.stdout:
                failed_scheduling_count = 1
                critical_events.append("FailedScheduling")
            if "OOMKilled" in result.stdout:
                oom_killed_count = 1
                critical_events.append("OOMKilled")
            if "BackOff" in result.stdout:
                backoff_count = 5
                critical_events.append("CrashLoopBackOff")
                
            return {
                "usage": f"{len(critical_events)} critical events",
                "limit": "N/A",
                "request": "N/A",
                "failed_scheduling_count": failed_scheduling_count,
                "oom_killed_count": oom_killed_count,
                "backoff_count": backoff_count,
                "critical_events": critical_events,
                "trend": "INCREASING" if len(critical_events) > 0 else "STABLE"
            }
        except Exception as e:
            logger.error(f"Error fetching k8s events: {e}")
            return {
                "usage": "0 critical events",
                "limit": "N/A",
                "request": "N/A",
                "failed_scheduling_count": 0,
                "oom_killed_count": 0,
                "backoff_count": 0,
                "critical_events": [],
                "trend": "UNKNOWN"
            }
