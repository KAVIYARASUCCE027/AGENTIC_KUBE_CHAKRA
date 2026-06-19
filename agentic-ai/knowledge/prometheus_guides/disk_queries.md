# Prometheus Disk Queries

## Persistent Volume (PV) Usage
To monitor the disk space utilization of a persistent volume attached to a pod:

```promql
kubelet_volume_stats_used_bytes{namespace="my-namespace", persistentvolumeclaim="my-pvc"}
/
kubelet_volume_stats_capacity_bytes{namespace="my-namespace", persistentvolumeclaim="my-pvc"} * 100
```
Alert if this exceeds 80-85%.

## Ephemeral Storage Usage
To monitor the ephemeral storage (scratch space, logs, emptyDirs) used by a pod:

```promql
container_fs_usage_bytes{namespace="my-namespace", pod="my-pod"}
```

## Node Disk Usage
To monitor the overall disk usage of the underlying Kubernetes node:

```promql
(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_free_bytes{mountpoint="/"})
/
node_filesystem_size_bytes{mountpoint="/"} * 100
```

## Disk I/O Wait Time (Bottleneck Detection)
To check if the node is experiencing disk I/O bottlenecks (which can cause applications to hang):

```promql
rate(node_cpu_seconds_total{mode="iowait"}[5m])
```
High `iowait` means CPUs are idle waiting for disk operations to complete.
