"""
Rollback Service — Phase 15.
"""
import os
import tempfile
import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RollbackService:
    """
    Handles rollback of executed Kubernetes actions.
    """

    def _run_kubectl(self, command: list[str]) -> tuple[bool, str]:
        cmd = ["kubectl"] + command
        cmd_str = " ".join(cmd)
        logger.info(f"Running rollback command: {cmd_str}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                logger.error(f"Rollback command failed: {result.stderr.strip()}")
                return False, result.stderr.strip()
        except Exception as e:
            logger.error(f"Error executing rollback kubectl: {e}")
            return False, str(e)

    def _apply_yaml_backup(self, namespace: str, backup_yaml: str) -> Dict[str, Any]:
        """
        Applies a saved YAML string to the cluster to restore state.
        """
        if not backup_yaml:
            return {"status": "FAILED", "message": "No backup YAML provided for rollback."}
            
        fd, path = tempfile.mkstemp(suffix=".yaml")
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(backup_yaml)
                
            success, msg = self._run_kubectl(["apply", "-f", path, "-n", namespace])
            return {
                "status": "SUCCESS" if success else "FAILED",
                "message": msg
            }
        finally:
            if os.path.exists(path):
                os.remove(path)

    def rollback_scale(self, namespace: str, deployment_name: str, backup_yaml: str) -> Dict[str, Any]:
        """
        Rollback a scaling action by reapplying the backup YAML.
        """
        return self._apply_yaml_backup(namespace, backup_yaml)

    def rollback_patch(self, namespace: str, deployment_name: str, backup_yaml: str) -> Dict[str, Any]:
        """
        Rollback resource patches by reapplying the backup YAML.
        """
        return self._apply_yaml_backup(namespace, backup_yaml)

    def rollback_restart(self, namespace: str, deployment_name: str) -> Dict[str, Any]:
        """
        Rollback a rollout restart using rollout undo.
        """
        success, msg = self._run_kubectl([
            "rollout", "undo", "deployment", deployment_name, "-n", namespace
        ])
        return {
            "status": "SUCCESS" if success else "FAILED",
            "message": msg
        }
