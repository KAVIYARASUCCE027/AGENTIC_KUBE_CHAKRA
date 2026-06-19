# Kubernetes Resource Requests and Limits

## Overview
When you specify a Pod, you can optionally specify how much of each resource a container needs. The most common resources to specify are CPU and memory (RAM).
- **Requests**: What the container is guaranteed to get. If a container requests a resource, Kubernetes will only schedule it on a node that can give it that resource.
- **Limits**: The maximum amount of resource the container is allowed to use. If it tries to use more than its limit, the system intervenes.

## CPU (Compressible Resource)
CPU is measured in cores (or millicores). `1` CPU equals `1000m`.
- **Requests**: Determines scheduling.
- **Limits**: Implemented via Linux cgroups (CPU quotas). If a container tries to use more CPU than its limit, it is **throttled**. The application slows down, but it is *not* terminated. High throttling can cause latency spikes and liveness probe failures.

## Memory (Incompressible Resource)
Memory is measured in bytes (Mi, Gi, etc.).
- **Requests**: Determines scheduling.
- **Limits**: Implemented via Linux cgroups. If a container tries to allocate more memory than its limit, the Linux kernel invokes the **OOM Killer** (Out Of Memory) and terminates the container process. The Pod will show `OOMKilled`.

## Quality of Service (QoS) Classes
Kubernetes uses requests and limits to assign a QoS class to a Pod. This class determines the Pod's priority when the node is under resource pressure and needs to evict pods.

1. **Guaranteed**:
   - Every container in the Pod must have a memory limit and a memory request.
   - For every container, memory limit must equal memory request.
   - Every container must have a CPU limit and a CPU request.
   - For every container, CPU limit must equal CPU request.
   - *Behavior*: These pods are the last to be evicted.

2. **Burstable**:
   - The Pod does not meet the criteria for Guaranteed.
   - At least one container has a memory or CPU request or limit.
   - *Behavior*: They can burst above their requests if resources are available, but will be evicted before Guaranteed pods if the node runs out of resources.

3. **BestEffort**:
   - The Pod has no memory or CPU requests or limits defined for any containers.
   - *Behavior*: These pods are the first to be killed if the node experiences resource pressure. They are purely "best effort".

## Best Practices
- Always set memory limits to prevent a single buggy application from consuming all node memory and crashing the node.
- Keep CPU limits relatively loose or omit them entirely in some environments, as CPU throttling can cause severe performance issues that are hard to debug, while CPU is a shared, compressible resource.
- Ensure requests are set accurately based on baseline profiling to allow the scheduler to pack nodes efficiently.
