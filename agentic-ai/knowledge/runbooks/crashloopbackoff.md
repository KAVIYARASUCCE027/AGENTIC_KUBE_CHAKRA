# CrashLoopBackOff Runbook

## Description
`CrashLoopBackOff` is not an error itself, but a state indicating that a container repeatedly fails to start or crashes shortly after starting. Kubernetes tries to restart it, but if it keeps failing, the delay between restarts increases exponentially (the "back-off").

## Symptoms
- Pod status shows `CrashLoopBackOff`.
- Restart count is high and increasing.
- Application is inaccessible.

## Common Causes
1. **Application Crash**: Unhandled exceptions, segmentation faults, or fatal errors in the code.
2. **Misconfiguration**: Missing environment variables, invalid config maps, or incorrect command-line arguments.
3. **Dependency Failures**: The application cannot connect to a required database, cache, or external API during startup.
4. **Liveness Probe Failure**: The application is running but failing its liveness probe, causing Kubernetes to kill and restart it.
5. **Resource Exhaustion**: The container immediately OOMKills on startup or gets CPU throttled so severely it fails probes.
6. **File Permission Issues**: The container user lacks permissions to read/write required files or directories.

## Troubleshooting Steps
1. **Check Pod Logs (Previous Instance)**:
   `kubectl logs <pod-name> -n <namespace> --previous`
   This is the most critical step to see *why* the last container crashed.
2. **Check Pod Events**:
   `kubectl describe pod <pod-name> -n <namespace>`
   Look for `Back-off restarting failed container` and check the events leading up to it.
3. **Verify Configuration**:
   Ensure all required ConfigMaps and Secrets are present and correctly formatted.
4. **Check Probes**:
   If logs don't show a crash, check if probes are failing: `kubectl describe pod ...`. Is the initialDelaySeconds too short?

## Remediation
- Fix application code if there's an unhandled exception.
- Correct environment variables, ConfigMaps, or Secrets.
- Fix network policies or connection strings if external dependencies are unreachable.
- Adjust Liveness/Readiness probe settings (e.g., increase `initialDelaySeconds` or `timeoutSeconds`).

## Preventive Measures
- Implement robust error handling and logging during application startup.
- Use InitContainers to verify dependencies (like databases) are available before the main app starts.
- Thoroughly test configurations in staging before deploying to production.
