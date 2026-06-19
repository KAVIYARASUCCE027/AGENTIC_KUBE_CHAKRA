# Prometheus CPU Queries

## CPU Usage over time (Rate)
To calculate the CPU usage of a specific container in cores over a time window (e.g., 5 minutes), use the `rate` function on the `container_cpu_usage_seconds_total` counter.

```promql
rate(container_cpu_usage_seconds_total{namespace="my-namespace", pod="my-pod", container="my-container"}[5m])
```

## CPU Throttling
CPU throttling occurs when a container attempts to use more CPU than its `limits.cpu`. To calculate the percentage of time a container is being throttled, compare the throttled periods to the total periods.

```promql
sum(rate(container_cpu_cfs_throttled_periods_total{namespace="my-namespace", pod="my-pod"}[5m]))
/
sum(rate(container_cpu_cfs_periods_total{namespace="my-namespace", pod="my-pod"}[5m])) * 100
```
If this value is > 0, the container is being throttled. A value > 10-20% usually indicates a severe performance impact.

## CPU Utilization vs Limit
To see how much of the allocated CPU limit a container is actually using:

```promql
rate(container_cpu_usage_seconds_total{namespace="my-namespace", pod="my-pod"}[5m])
/
(kube_pod_container_resource_limits{resource="cpu", namespace="my-namespace", pod="my-pod"})
```

## Node CPU Utilization
To check if the underlying node is running out of CPU capacity (which could lead to scheduling issues or CPU contention):

```promql
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```
