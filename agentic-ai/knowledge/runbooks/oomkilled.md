# OOMKilled Runbook

## Description
OOMKilled (Out Of Memory Killed) indicates that a container's memory usage exceeded its configured `limits.memory`. The Linux OOM Killer terminated the container to prevent it from consuming all available node memory.

## Symptoms
- Pod status shows `OOMKilled`.
- Container restart count is increasing.
- Exit code 137 in container logs/status.
- Node memory pressure (sometimes, if limits weren't set and the pod exhausted node memory).

## Common Causes
1. **Memory Leak**: The application does not properly release memory over time.
2. **Spike in Traffic/Load**: The application legitimately needs more memory to process a sudden influx of requests.
3. **Misconfigured Limits**: The `limits.memory` is set too low for the application's normal baseline usage.
4. **Large Data Processing**: The application is trying to load a massive file or dataset into memory all at once.

## Troubleshooting Steps
1. **Check Pod Status and Events**:
   `kubectl describe pod <pod-name> -n <namespace>`
   Look for `State: Terminated`, `Reason: OOMKilled`, and `Exit Code: 137`.
2. **Review Resource Requests and Limits**:
   Check the pod's YAML. Does it have memory requests and limits defined? Are they realistic?
3. **Analyze Memory Metrics**:
   Query Prometheus for the container's memory usage over time. Does it show a steady climb (leak) or a sudden spike?
4. **Check Application Logs**:
   Look for OutOfMemory exceptions (e.g., `java.lang.OutOfMemoryError` in Java, fatal errors in Node.js/Go) right before the crash.

## Remediation
- **Short-term**: If the limit is clearly too low, increase the `limits.memory` in the deployment and rolling restart.
- **Long-term**: Profile the application to identify and fix memory leaks. Optimize data structures or batch processing to reduce peak memory footprint. Implement proper garbage collection tuning.

## Preventive Measures
- Set appropriate memory requests and limits based on historical usage.
- Configure autoscaling (HPA) based on memory utilization.
- Implement alerting for memory usage approaching the limit (e.g., >85% of limit).
- Profile memory usage during CI/CD load testing.
