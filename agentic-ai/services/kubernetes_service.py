"""
Kubernetes Service — Phase 15.
"""
import subprocess
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class KubernetesService:
    """
    Service for executing kubectl commands via subprocess.
    """

    def _run_kubectl(self, command: list[str]) -> Tuple[bool, str, str]:
        """
        Helper to run kubectl commands.
        Returns: (success_boolean, stdout, stderr)
        """
        cmd = ["kubectl"] + command
        cmd_str = " ".join(cmd)
        logger.info(f"Running kubectl command: {cmd_str}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            success = result.returncode == 0
            if not success:
                logger.warning(f"kubectl command failed. Stderr: {result.stderr.strip()}")
            return success, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            logger.error(f"Error executing kubectl: {e}")
            return False, "", str(e)

    def backup_deployment(self, namespace: str, deployment_name: str) -> Optional[str]:
        """
        Saves the current deployment YAML as a string.
        """
        success, stdout, stderr = self._run_kubectl([
            "get", "deployment", deployment_name,
            "-n", namespace,
            "-o", "yaml"
        ])
        if success:
            return stdout
        return None

    def scale_deployment(self, namespace: str, deployment_name: str, replicas: int) -> Dict[str, Any]:
        """
        Scale deployment to a specific replica count.
        """
        success, stdout, stderr = self._run_kubectl([
            "scale", "deployment", deployment_name,
            f"--replicas={replicas}",
            "-n", namespace
        ])
        return {
            "status": "SUCCESS" if success else "FAILED",
            "message": stdout if success else stderr,
            "command": f"kubectl scale deployment {deployment_name} --replicas={replicas} -n {namespace}"
        }

    def rollout_restart(self, namespace: str, deployment_name: str) -> Dict[str, Any]:
        """
        Trigger a rolling restart of the deployment.
        """
        success, stdout, stderr = self._run_kubectl([
            "rollout", "restart", "deployment", deployment_name,
            "-n", namespace
        ])
        return {
            "status": "SUCCESS" if success else "FAILED",
            "message": stdout if success else stderr,
            "command": f"kubectl rollout restart deployment {deployment_name} -n {namespace}"
        }

    def patch_cpu(self, namespace: str, deployment_name: str, cpu_limit: str) -> Dict[str, Any]:
        """
        Patch deployment CPU limit using set resources.
        """
        # We apply the limit to all containers in the deployment for simplicity
        cmd = [
            "set", "resources", "deployment", deployment_name,
            "-c=*",
            f"--limits=cpu={cpu_limit}",
            f"--requests=cpu={cpu_limit}",
            "-n", namespace
        ]
        success, stdout, stderr = self._run_kubectl(cmd)
        return {
            "status": "SUCCESS" if success else "FAILED",
            "message": stdout if success else stderr,
            "command": " ".join(["kubectl"] + cmd)
        }

    def patch_memory(self, namespace: str, deployment_name: str, memory_limit: str) -> Dict[str, Any]:
        """
        Patch deployment Memory limit using set resources.
        """
        cmd = [
            "set", "resources", "deployment", deployment_name,
            "-c=*",
            f"--limits=memory={memory_limit}",
            f"--requests=memory={memory_limit}",
            "-n", namespace
        ]
        success, stdout, stderr = self._run_kubectl(cmd)
        return {
            "status": "SUCCESS" if success else "FAILED",
            "message": stdout if success else stderr,
            "command": " ".join(["kubectl"] + cmd)
        }

    def create_hpa(self, namespace: str, deployment_name: str, cpu_percent: int = 70, min_replicas: int = 2, max_replicas: int = 10) -> Dict[str, Any]:
        """
        Create a HorizontalPodAutoscaler for the deployment.
        """
        cmd = [
            "autoscale", "deployment", deployment_name,
            f"--cpu-percent={cpu_percent}",
            f"--min={min_replicas}",
            f"--max={max_replicas}",
            "-n", namespace
        ]
        success, stdout, stderr = self._run_kubectl(cmd)
        return {
            "status": "SUCCESS" if success else "FAILED",
            "message": stdout if success else stderr,
            "command": " ".join(["kubectl"] + cmd)
        }

    def verify_execution(self, namespace: str, deployment_name: str) -> Tuple[bool, str]:
        """
        Verify the execution by checking the deployment status.
        """
        # Check rollout status
        success, stdout, stderr = self._run_kubectl([
            "rollout", "status", "deployment", deployment_name,
            "-n", namespace,
            "--timeout=30s"
        ])
        
        if success:
            return True, stdout
        else:
            return False, stderr
