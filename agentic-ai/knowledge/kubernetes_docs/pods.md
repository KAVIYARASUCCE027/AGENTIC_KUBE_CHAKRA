# Kubernetes Pods

## Overview
A Pod is the smallest, most basic deployable object in Kubernetes. A Pod represents a single instance of a running process in your cluster. Pods contain one or more containers, such as Docker containers. When a Pod runs multiple containers, the containers are managed as a single entity and share the Pod's resources.

## Key Characteristics
- **Shared Network Namespace**: Containers in a Pod share the same IP address and port space. They can communicate with each other using `localhost`.
- **Shared Storage**: Containers in a Pod can share access to volumes, allowing them to read and write the same files.
- **Ephemeral Nature**: Pods are designed to be relatively ephemeral (not durable). When a Pod dies, it is not resurrected. Controllers like Deployments or StatefulSets manage recreating Pods.

## Lifecycle Phases
1. **Pending**: The Pod has been accepted by the cluster, but one or more container images have not been created. This includes time waiting to be scheduled as well as downloading images over the network.
2. **Running**: The Pod has been bound to a node, and all of the containers have been created. At least one container is still running, or is in the process of starting or restarting.
3. **Succeeded**: All containers in the Pod have terminated in success, and will not be restarted.
4. **Failed**: All containers in the Pod have terminated, and at least one container has terminated in failure. That is, the container either exited with non-zero status or was terminated by the system.
5. **Unknown**: For some reason the state of the Pod could not be obtained, typically due to an error in communicating with the host of the Pod.

## Multi-Container Patterns
- **Sidecar**: A secondary container that adds functionality to the primary container (e.g., logging agents, proxy servers like Envoy).
- **Ambassador**: A container that proxies network connections to the primary container.
- **Adapter**: A container that standardizes and normalizes the output of the primary container (e.g., normalizing log formats).

## Init Containers
Pods can have one or more init containers, which are run before the app containers are started. Init containers must run to completion before the next init container starts, and all init containers must complete successfully before the app containers launch. They are often used to delay application startup until a precondition is met (e.g., a database is ready).
