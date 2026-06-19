# Prometheus Memory Queries

## Container Memory Usage (Working Set)
The most important metric for memory in Kubernetes is `container_memory_working_set_bytes`. This is what the OOM Killer watches. It excludes cached data that can be evicted by the OS under memory pressure.

```promql
container_memory_working_set_bytes{namespace="my-namespace", pod="my-pod", container="my-container"}
```

## Memory Utilization vs Limit (OOM Risk)
To see how close a container is to hitting its memory limit (and being OOMKilled):

```promql
container_memory_working_set_bytes{namespace="my-namespace", pod="my-pod"}
/
kube_pod_container_resource_limits{resource="memory", namespace="my-namespace", pod="my-pod"} * 100
```
If this approaches 100%, an OOMKill is imminent.

## Detecting Memory Leaks
To mathematically detect a memory leak over a long period (e.g., 24 hours), you can use the `deriv` (derivative) function to see if the baseline memory is constantly increasing.

```promql
deriv(container_memory_working_set_bytes{namespace="my-namespace", pod="my-pod"}[1h])
```
A consistently positive value over a long time window, independent of traffic patterns, strongly suggests a leak.

## Node Memory Utilization
To check if the underlying node is under memory pressure:

```promql
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100
```
