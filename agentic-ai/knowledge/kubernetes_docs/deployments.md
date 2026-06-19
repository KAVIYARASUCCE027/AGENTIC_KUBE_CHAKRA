# Kubernetes Deployments

## Overview
A Deployment provides declarative updates for Pods and ReplicaSets. You describe a desired state in a Deployment, and the Deployment Controller changes the actual state to the desired state at a controlled rate. You can define Deployments to create new ReplicaSets, or to remove existing Deployments and adopt all their resources with new Deployments.

## Key Capabilities
- **Rollout a ReplicaSet**: Deployments manage ReplicaSets, which in turn ensure the desired number of Pods are running.
- **Declare New State**: Update the PodTemplateSpec of the Deployment to trigger a rollout to a new version.
- **Rollback**: If the current state of a Deployment is not stable (e.g., CrashLoopBackOff), you can roll back to an earlier Deployment revision.
- **Scale**: Scale the Deployment to facilitate more load.
- **Pause/Resume**: Pause the rollout of a Deployment to apply multiple fixes to its PodTemplateSpec, then resume it to start a new rollout.

## Update Strategies
1. **RollingUpdate (Default)**: Replaces old Pods with new ones gradually. This guarantees zero downtime during updates. It respects `maxUnavailable` (maximum number of Pods that can be unavailable during the update) and `maxSurge` (maximum number of Pods that can be scheduled above the desired number of Pods).
2. **Recreate**: All existing Pods are killed before new ones are created. This will result in downtime during the update process but guarantees that old and new versions do not run concurrently.

## Use Cases
Deployments are the most common way to deploy stateless applications in Kubernetes (e.g., web servers, APIs, microservices). They are not suited for applications that require stable network identities or persistent storage attached to specific instances (use StatefulSets for those).

## Best Practices
- Always use Deployments (or other controllers) to manage Pods; never create naked Pods.
- Specify resource requests and limits in the PodTemplate.
- Configure proper readiness and liveness probes so the Deployment controller knows when new Pods are actually ready to receive traffic during a rolling update.
- Use meaningful labels and selectors to tie the Deployment to its corresponding Service.
