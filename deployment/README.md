# Advanced Deployment Strategies

This directory contains Kubernetes deployment configurations for advanced deployment strategies.

## Canary Deployment

**File:** `canary.yaml`

Canary deployment gradually rolls out new versions to a small subset of users before full deployment.

### Features:
- Stable deployment (3 replicas) serving majority of traffic
- Canary deployment (1 replica) receiving 10% of traffic
- Traffic splitting via Nginx Ingress annotations
- Can be triggered by header (`X-Canary: true`)

### Usage:

1. Deploy stable version:
```bash
kubectl apply -f canary.yaml
```

2. Update canary image:
```bash
kubectl set image deployment/ai-service-canary ai-service=woragis/ai-service:v1.2.0
```

3. Monitor canary metrics:
```bash
# Check canary pod logs
kubectl logs -f deployment/ai-service-canary

# Check metrics
kubectl port-forward svc/ai-service 8080:80
curl http://localhost:8080/metrics
```

4. Promote canary to stable:
```bash
# Update stable deployment
kubectl set image deployment/ai-service-stable ai-service=woragis/ai-service:v1.2.0

# Scale down canary
kubectl scale deployment/ai-service-canary --replicas=0
```

5. Rollback if needed:
```bash
# Scale down canary
kubectl scale deployment/ai-service-canary --replicas=0
```

## Blue-Green Deployment

**File:** `blue-green.yaml`

Blue-green deployment maintains two identical production environments and switches traffic instantly.

### Features:
- Blue environment (current production)
- Green environment (new version)
- Instant traffic switch via service selector
- Zero-downtime deployments
- Easy rollback

### Usage:

1. Deploy blue (current version):
```bash
kubectl apply -f blue-green.yaml
```

2. Deploy green (new version):
```bash
# Update green deployment image
kubectl set image deployment/ai-service-green ai-service=woragis/ai-service:v1.2.0

# Wait for green to be ready
kubectl rollout status deployment/ai-service-green
```

3. Switch traffic to green:
```bash
kubectl patch service ai-service -p '{"spec":{"selector":{"version":"green"}}}'
```

4. Monitor green environment:
```bash
# Check green pod logs
kubectl logs -f deployment/ai-service-green

# Check metrics
kubectl port-forward svc/ai-service 8080:80
curl http://localhost:8080/metrics
```

5. Rollback to blue (if needed):
```bash
kubectl patch service ai-service -p '{"spec":{"selector":{"version":"blue"}}}'
```

6. Clean up old blue deployment (after confirming green works):
```bash
kubectl delete deployment ai-service-blue
```

## Deployment Best Practices

1. **Health Checks**: Always configure liveness and readiness probes
2. **Resource Limits**: Set appropriate CPU and memory limits
3. **Gradual Rollout**: Use canary for risky changes, blue-green for safe changes
4. **Monitoring**: Monitor metrics during deployment
5. **Rollback Plan**: Always have a rollback strategy ready
6. **Testing**: Test deployments in staging first

## Monitoring During Deployment

Monitor these metrics during deployment:
- Request rate
- Error rate
- Latency (P95, P99)
- CPU and memory usage
- Health check status

Use Prometheus queries:
```promql
# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Latency P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Request rate
rate(http_requests_total[5m])
```

