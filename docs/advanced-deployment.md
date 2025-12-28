# Advanced Deployment Guide

This guide explains advanced deployment strategies for the AI Service, including canary and blue-green deployments.

## Overview

Advanced deployment strategies enable zero-downtime deployments, gradual rollouts, and easy rollbacks. Two strategies are supported:

1. **Canary Deployment** - Gradual rollout to a subset of users
2. **Blue-Green Deployment** - Instant switch between two environments

## Canary Deployment

### What is Canary Deployment?

Canary deployment gradually rolls out a new version to a small percentage of users before full deployment. This allows you to:
- Test new versions in production with real traffic
- Monitor metrics before full rollout
- Rollback quickly if issues are detected

### How It Works

1. **Stable Deployment** (3 replicas) - Serves 90% of traffic
2. **Canary Deployment** (1 replica) - Serves 10% of traffic
3. **Traffic Splitting** - Nginx Ingress splits traffic based on weight
4. **Monitoring** - Monitor canary metrics
5. **Promotion** - Promote canary to stable if successful
6. **Rollback** - Scale down canary if issues detected

### Configuration

Deployment configuration is in `deployment/canary.yaml`:

- **Stable Deployment**: `ai-service-stable` (3 replicas)
- **Canary Deployment**: `ai-service-canary` (1 replica)
- **Service**: Routes to both deployments
- **Ingress**: Splits traffic 90/10 (configurable)

### Usage

#### 1. Deploy Initial Setup

```bash
kubectl apply -f deployment/canary.yaml
```

#### 2. Deploy New Version to Canary

```bash
# Update canary image
kubectl set image deployment/ai-service-canary \
  ai-service=woragis/ai-service:v1.2.0

# Wait for rollout
kubectl rollout status deployment/ai-service-canary
```

#### 3. Monitor Canary

```bash
# Check canary pod logs
kubectl logs -f deployment/ai-service-canary

# Check canary metrics
kubectl port-forward svc/ai-service 8080:80
curl http://localhost:8080/metrics | grep canary

# Compare stable vs canary metrics
# - Error rates
# - Latency
# - Throughput
```

#### 4. Increase Canary Traffic (Optional)

Gradually increase canary traffic:

```bash
# Update ingress annotation to 25%
kubectl annotate ingress ai-service-ingress \
  nginx.ingress.kubernetes.io/canary-weight="25" --overwrite

# Monitor for issues, then increase to 50%, 75%, 100%
```

#### 5. Promote Canary to Stable

```bash
# Update stable deployment
kubectl set image deployment/ai-service-stable \
  ai-service=woragis/ai-service:v1.2.0

# Wait for stable rollout
kubectl rollout status deployment/ai-service-stable

# Scale down canary
kubectl scale deployment/ai-service-canary --replicas=0
```

#### 6. Rollback (If Needed)

```bash
# Scale down canary immediately
kubectl scale deployment/ai-service-canary --replicas=0

# Stable continues serving all traffic
```

### Monitoring During Canary

Monitor these metrics:
- Error rate (should be similar to stable)
- Latency (should be similar to stable)
- Request rate (should match traffic split)
- Resource usage (CPU, memory)

### Best Practices

1. **Start Small**: Begin with 5-10% traffic
2. **Monitor Closely**: Watch metrics for 15-30 minutes
3. **Gradual Increase**: Increase traffic gradually if successful
4. **Have Rollback Plan**: Be ready to rollback quickly
5. **Test First**: Test in staging before production

## Blue-Green Deployment

### What is Blue-Green Deployment?

Blue-green deployment maintains two identical production environments. Traffic switches instantly from blue (current) to green (new). This enables:
- Zero-downtime deployments
- Instant rollback
- Testing new version before traffic switch

### How It Works

1. **Blue Environment** (current production) - Serves all traffic
2. **Green Environment** (new version) - Deployed but idle
3. **Service Switch** - Service selector switches from blue to green
4. **Traffic Switch** - All traffic goes to green instantly
5. **Rollback** - Switch back to blue if needed

### Configuration

Deployment configuration is in `deployment/blue-green.yaml`:

- **Blue Deployment**: `ai-service-blue` (current version)
- **Green Deployment**: `ai-service-green` (new version)
- **Service**: Routes to blue or green via selector

### Usage

#### 1. Deploy Initial Setup

```bash
kubectl apply -f deployment/blue-green.yaml
```

#### 2. Deploy New Version to Green

```bash
# Update green deployment image
kubectl set image deployment/ai-service-green \
  ai-service=woragis/ai-service:v1.2.0

# Wait for green to be ready
kubectl rollout status deployment/ai-service-green

# Verify green is healthy
kubectl get pods -l version=green
```

#### 3. Test Green Environment

```bash
# Port-forward to green pods directly
kubectl port-forward deployment/ai-service-green 8080:8080

# Test endpoints
curl http://localhost:8080/healthz
curl http://localhost:8080/v1/agents
```

#### 4. Switch Traffic to Green

```bash
# Switch service selector to green
kubectl patch service ai-service \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Verify traffic is going to green
kubectl get pods -l version=green
# Should see increased traffic
```

#### 5. Monitor Green Environment

```bash
# Check green pod logs
kubectl logs -f deployment/ai-service-green

# Check metrics
kubectl port-forward svc/ai-service 8080:80
curl http://localhost:8080/metrics
```

#### 6. Rollback to Blue (If Needed)

```bash
# Switch service selector back to blue
kubectl patch service ai-service \
  -p '{"spec":{"selector":{"version":"blue"}}}'

# Traffic immediately switches back to blue
```

#### 7. Clean Up Blue (After Confirming Green Works)

```bash
# After confirming green works for 24-48 hours
kubectl delete deployment ai-service-blue

# Update blue deployment for next release
kubectl apply -f deployment/blue-green.yaml
# (with new version in blue)
```

### Monitoring During Blue-Green

Monitor these metrics:
- Error rate (should remain stable)
- Latency (should remain stable)
- Request rate (should match normal traffic)
- Resource usage (CPU, memory)

### Best Practices

1. **Test Green First**: Test green environment before switching
2. **Monitor Closely**: Watch metrics for 15-30 minutes after switch
3. **Keep Blue Ready**: Don't delete blue immediately
4. **Have Rollback Plan**: Be ready to switch back quickly
5. **Gradual Rollout**: Consider canary for risky changes

## Choosing a Strategy

### Use Canary When:
- You want gradual rollout
- You want to test with real traffic
- You have limited resources
- Changes are low-risk

### Use Blue-Green When:
- You want instant switch
- You want zero downtime
- You have sufficient resources
- Changes are high-risk
- You need easy rollback

## Comparison

| Feature | Canary | Blue-Green |
|---------|--------|------------|
| Rollout Speed | Gradual | Instant |
| Resource Usage | Lower | Higher |
| Risk | Lower | Higher |
| Rollback | Gradual | Instant |
| Testing | Real traffic | Before switch |
| Complexity | Medium | Low |

## Troubleshooting

### Canary Issues

**Canary receiving no traffic:**
- Check ingress annotations
- Verify service selector
- Check pod labels

**Canary metrics different:**
- Normal if traffic is low
- Check for actual issues
- Compare error rates

### Blue-Green Issues

**Traffic not switching:**
- Check service selector
- Verify pod labels
- Check service endpoints

**Green not ready:**
- Check pod status
- Check health probes
- Review logs

## References

- [Kubernetes Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#deployment-strategies)
- [Nginx Ingress Canary](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/#canary)
- [Blue-Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)

