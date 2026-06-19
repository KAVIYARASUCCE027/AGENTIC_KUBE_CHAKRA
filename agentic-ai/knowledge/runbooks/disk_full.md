# Disk Full (Storage Exhaustion) Runbook

## Description
Disk full or storage exhaustion occurs when a pod or the underlying Kubernetes node runs out of available disk space. This can lead to application crashes, data loss, inability to write logs, and even node instability (e.g., `DiskPressure` node condition causing pod evictions).

## Symptoms
- Application logs show `No space left on device` or `IOException`.
- Pod status shows `Evicted` with reason `DiskPressure`.
- Node status shows `DiskPressure` condition as `True`.
- Prometheus metrics show volume or node disk usage at or near 100%.

## Common Causes
1. **Unbounded Logging**: Application writing excessive logs to stdout/stderr or a local file without log rotation.
2. **Ephemeral Storage Exhaustion**: The container is writing too many temporary files to its writable layer or `emptyDir` volumes.
3. **Persistent Volume (PV) Full**: A database or stateful application has filled its allocated PV.
4. **Core Dumps**: Application crashing repeatedly and generating large core dump files.
5. **Container Image Sprawl**: The node's container runtime storage is full of old, unused container images (usually handled by kubelet GC, but can fail).

## Troubleshooting Steps
1. **Identify the Scope**:
   Is it a single Pod's PV, a Pod's ephemeral storage, or the entire Node?
2. **Check Pod Events**:
   `kubectl describe pod <pod-name> -n <namespace>`
   Look for eviction notices due to `DiskPressure` or ephemeral storage limits exceeded.
3. **Check Node Status**:
   `kubectl describe node <node-name>`
   Look for `DiskPressure` in the Conditions section.
4. **Inspect Volume Usage**:
   Exec into the pod and use `df -h` or `du -sh *` to find the largest directories.
   For PVs, check the underlying storage provisioner metrics.

## Remediation
- **Ephemeral Storage**: Clear temporary files. If logging to files, configure log rotation. Increase `limits.ephemeral-storage` if the application legitimately needs more scratch space.
- **Persistent Volumes**: Expand the PVC (if the storage class supports `allowVolumeExpansion`). Alternatively, clean up old data or implement data retention policies in the application.
- **Node Level**: If the node is full, trigger a manual image prune (`crictl rmi --prune`) or investigate what is consuming space on the host OS.

## Preventive Measures
- Set `requests.ephemeral-storage` and `limits.ephemeral-storage` on all pods to prevent noisy neighbors from exhausting node disk space.
- Implement strict log rotation policies.
- Set up Prometheus alerts for PV utilization > 80% and Node disk utilization > 85%.
- Regularly clean up temporary files in application code.
