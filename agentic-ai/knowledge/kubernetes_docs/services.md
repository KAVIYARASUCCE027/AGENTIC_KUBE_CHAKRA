# Kubernetes Services

## Overview
In Kubernetes, a Service is an abstraction which defines a logical set of Pods and a policy by which to access them (sometimes this pattern is called a micro-service). The set of Pods targeted by a Service is usually determined by a selector.

Because Pods are ephemeral and their IP addresses change when they are recreated (e.g., by a Deployment), Services provide a stable IP address and DNS name that other applications can use to connect to the Pods.

## Service Types

1. **ClusterIP (Default)**
   - Exposes the Service on a cluster-internal IP.
   - Makes the Service only reachable from within the cluster.
   - Used for internal microservice-to-microservice communication.

2. **NodePort**
   - Exposes the Service on each Node's IP at a static port (the NodePort).
   - A ClusterIP Service, to which the NodePort Service routes, is automatically created.
   - You can contact the NodePort Service from outside the cluster by requesting `<NodeIP>:<NodePort>`.
   - Often used for local development or simple external access.

3. **LoadBalancer**
   - Exposes the Service externally using a cloud provider's load balancer (e.g., AWS ELB, GCP Load Balancer).
   - NodePort and ClusterIP Services are created automatically, to which the external load balancer routes.
   - Used for exposing web applications to the public internet.

4. **ExternalName**
   - Maps the Service to the contents of the `externalName` field (e.g., `foo.bar.example.com`), by returning a `CNAME` record with its value.
   - No proxying of any kind is set up.
   - Useful for abstracting external services (like a managed database outside the cluster) as if they were internal Kubernetes services.

## DNS Resolution
Kubernetes clusters use CoreDNS to manage DNS records for Services and Pods. When you create a Service named `my-service` in the namespace `my-namespace`, a DNS record is automatically created:
`my-service.my-namespace.svc.cluster.local`

Pods within the same namespace can resolve the service just by using `my-service`. Pods in other namespaces must use `my-service.my-namespace`.

## Endpoints and EndpointSlices
When a Service with a selector is created, the Kubernetes Endpoint controller continuously scans for Pods that match the selector and updates an `Endpoints` (or `EndpointSlice`) object with their IP addresses. If a Pod fails its readiness probe, its IP is removed from the Endpoints list, and the Service stops routing traffic to it.
