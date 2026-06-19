# Horizontal Pod Autoscaler (HPA)

## Overview
The Horizontal Pod Autoscaler automatically updates a workload resource (such as a Deployment or StatefulSet), with the aim of automatically scaling the workload to match demand. Horizontal scaling means that the response to increased load is to deploy more Pods. This is different from vertical scaling, which for Kubernetes would mean assigning more resources (for example: memory or CPU) to the pods that are already running for the workload.

## How it Works
HPA is implemented as a Kubernetes API resource and a controller. The controller periodically queries the resource metrics API (usually provided by Metrics Server) to fetch metrics for the target pods.
If the observed metric value exceeds the target threshold, the HPA instructs the workload controller (like the Deployment) to scale up. If it falls below the threshold, it scales down.

## Metric Types
1. **Resource Metrics**: Standard container metrics like CPU and Memory usage. Often expressed as a percentage of the requested value.
   - Example: Target 80% average CPU utilization across all pods.
2. **Custom Metrics**: Metrics provided by the application itself or other systems (e.g., Queue length, HTTP request rate). Requires a Custom Metrics adapter (like Prometheus Adapter).
3. **External Metrics**: Metrics from outside the Kubernetes cluster (e.g., Cloud provider queue metrics).

## Configuration Requirements
- **Metrics Server**: Must be installed in the cluster for CPU/Memory scaling to work.
- **Resource Requests**: The target Pods *must* have resource requests defined for the metric being scaled on (e.g., CPU requests). If requests are missing, the HPA cannot calculate the utilization percentage and scaling will fail.

## Algorithm
The basic HPA algorithm calculates the desired number of replicas using this formula:
`desiredReplicas = ceil[currentReplicas * ( currentMetricValue / desiredMetricValue )]`

## Stabilization Window
To prevent "flapping" (rapid scaling up and down), HPA uses a stabilization window. By default, scale-down operations are delayed by a stabilization window (usually 5 minutes) to ensure the metric drop is consistent and not just a temporary dip.

## Troubleshooting HPA
- If HPA shows `<unknown>` for metrics, verify that Metrics Server is running and the target pods have resource `requests` defined.
- If HPA scales up but pods stay `Pending`, the cluster might not have enough node capacity (consider Cluster Autoscaler).
- If HPA is scaling too aggressively, adjust the target percentages or implement custom metrics that better reflect actual load.
