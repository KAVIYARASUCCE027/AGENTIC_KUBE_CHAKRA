# Memory Leak Runbook

## Description
A memory leak occurs when an application allocates memory but fails to release it back to the operating system when it's no longer needed. In a containerized environment, this inevitably leads to the container consuming its entire memory limit and being OOMKilled.

## Symptoms
- Steady, linear or sawtooth upward trend in container memory usage over time.
- Frequent `OOMKilled` events followed by container restarts.
- Application performance degradation (increased garbage collection pauses, slower response times) as memory fills up.

## Common Causes
1. **Unclosed Resources**: Forgetting to close database connections, file handles, or network sockets.
2. **Caching Issues**: Unbounded in-memory caches that grow indefinitely without eviction policies (e.g., missing LRU or TTL).
3. **Global Variables/Static Collections**: Accumulating objects in static lists, maps, or global variables that live for the lifetime of the application.
4. **Event Listener Leaks**: Registering event listeners but failing to unregister them when the object is destroyed.
5. **Session Data**: Storing too much data in user sessions without expiring them.

## Troubleshooting Steps
1. **Analyze Memory Metrics**:
   View Prometheus graphs for `container_memory_working_set_bytes`. A classic leak shows a jagged "sawtooth" pattern: memory climbs steadily until it hits the limit, drops sharply (OOMKill), and starts climbing again.
2. **Compare with Traffic**:
   Does memory increase independently of traffic, or is it directly proportional? If it increases with traffic but doesn't drop when traffic subsides, it's likely a leak.
3. **Capture a Heap Dump**:
   If possible, capture a memory/heap dump from the running container *before* it OOMKills.
   - Java: `jmap` or `jcmd`
   - Node.js: `v8.writeHeapSnapshot()`
   - Go: `pprof`
4. **Analyze the Dump**:
   Use tools like Eclipse MAT, Chrome DevTools, or `go tool pprof` to identify which objects are consuming the most memory and what is holding references to them.

## Remediation
- **Immediate Mitigation**: Temporarily increase the container's memory limit to buy time, or set up automated restarts before the OOM limit is reached to avoid sudden crashes during peak traffic.
- **Root Cause Fix**: Identify the leaking code using heap dump analysis and fix it (e.g., implement cache eviction, close resources in `finally` blocks, fix event listener cleanup).

## Preventive Measures
- Implement memory usage alerts that trigger well before the OOM limit (e.g., alert if usage > 80% and trending upwards).
- Use bounded caches (e.g., LRU cache) instead of raw HashMaps for caching.
- Incorporate memory profiling and load testing into the CI/CD pipeline.
