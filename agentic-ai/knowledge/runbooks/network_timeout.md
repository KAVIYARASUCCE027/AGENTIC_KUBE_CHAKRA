# Network Timeout Runbook

## Description
A network timeout occurs when an application attempts to establish a connection or wait for a response from an external service, database, or another microservice, but does not receive a reply within the configured time limit.

## Symptoms
- Increased API latency and 5xx HTTP errors (often 504 Gateway Timeout).
- Application logs show `ConnectionTimeout`, `ReadTimeout`, `context deadline exceeded`, or similar errors.
- Dependency health checks fail.
- Potential cascading failures as threads/connections are held waiting for responses.

## Common Causes
1. **Downstream Service Degradation**: The target service is overloaded, crashing, or experiencing high latency itself.
2. **Network Partition/Routing Issues**: Dropped packets, misconfigured NetworkPolicies, or issues with the CNI (e.g., Calico, Flannel) preventing traffic from reaching the destination.
3. **DNS Resolution Failure**: CoreDNS is overloaded or misconfigured, causing delays in resolving the target service's hostname.
4. **SNAT Port Exhaustion**: The node has run out of ephemeral ports for outbound connections, often due to a massive spike in outbound requests without connection pooling.
5. **Database Locks/Slow Queries**: The downstream database is locking tables or executing unoptimized queries, delaying responses.

## Troubleshooting Steps
1. **Identify the Target**:
   Look at the error logs. *Which* service is timing out?
2. **Check Downstream Health**:
   Is the target service healthy? Check its CPU, memory, and logs. Does it have pending pods?
3. **Check DNS**:
   Exec into the pod and run `nslookup <target-service>`. Is it resolving quickly? If not, check CoreDNS logs and metrics.
4. **Check Network Policies**:
   Did a recent deployment introduce a NetworkPolicy that blocks traffic between these pods?
5. **Analyze Metrics**:
   Check Prometheus for `coredns_dns_request_duration_seconds_bucket` or CNI metrics for dropped packets. Check the application's connection pool metrics.

## Remediation
- **Immediate**: If the downstream service is overloaded, scale it up (increase replicas). If it's a slow database query, identify and kill the offending query.
- **Configuration**: Adjust timeout settings in the application client to be realistic. Implement retries with exponential backoff and jitter.
- **Circuit Breakers**: Implement circuit breakers (e.g., using Istio or application libraries) to fail fast and prevent cascading exhaustion of threads.

## Preventive Measures
- Always configure explicit timeouts on all network calls; never rely on default infinite timeouts.
- Use connection pooling for databases and external APIs.
- Monitor CoreDNS latency and scale CoreDNS replicas as cluster size grows.
- Use service meshes or tracing (e.g., Jaeger) to visualize inter-service latency and identify bottlenecks.
