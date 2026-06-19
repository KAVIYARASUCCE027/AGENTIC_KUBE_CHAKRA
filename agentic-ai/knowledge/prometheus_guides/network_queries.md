# Prometheus Network Queries

## Network Throughput (Bytes Received/Transmitted)
To measure the total network bandwidth consumed by a pod:

**Bytes Received (Ingress):**
```promql
sum by (pod) (rate(container_network_receive_bytes_total{namespace="my-namespace", pod="my-pod"}[5m]))
```

**Bytes Transmitted (Egress):**
```promql
sum by (pod) (rate(container_network_transmit_bytes_total{namespace="my-namespace", pod="my-pod"}[5m]))
```

## Network Errors and Drops
To identify network-level drops or errors (could indicate CNI issues or full queues):

```promql
rate(container_network_receive_errors_total{namespace="my-namespace", pod="my-pod"}[5m])
rate(container_network_receive_drop_total{namespace="my-namespace", pod="my-pod"}[5m])
```

## CoreDNS Latency (DNS Resolution)
DNS is a critical dependency. High DNS latency will cause network timeouts in applications.

```promql
histogram_quantile(0.99, sum(rate(coredns_dns_request_duration_seconds_bucket[5m])) by (le))
```
This query returns the 99th percentile latency for CoreDNS requests in seconds.

## HTTP Request Rate (Application Level)
If using an ingress controller (like NGINX) or service mesh (like Istio), you can track application-level request rates and error rates.

**Total Request Rate (NGINX Ingress):**
```promql
sum(rate(nginx_ingress_controller_requests{namespace="my-namespace", ingress="my-ingress"}[5m]))
```

**5xx Error Rate:**
```promql
sum(rate(nginx_ingress_controller_requests{status=~"5.*", namespace="my-namespace", ingress="my-ingress"}[5m]))
/
sum(rate(nginx_ingress_controller_requests{namespace="my-namespace", ingress="my-ingress"}[5m])) * 100
```
