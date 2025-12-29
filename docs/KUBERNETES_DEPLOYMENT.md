# Kubernetes Deployment

## Overview

The AI service is designed to run in Kubernetes environments with support for advanced deployment strategies, monitoring, and scaling.

## Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Docker registry access (for image pulls)
- Persistent storage (for Qdrant vector database)

## Basic Deployment

### 1. Create Namespace

```bash
kubectl create namespace ai-service
```

### 2. Create Secrets

Create secrets for API keys:

```bash
kubectl create secret generic ai-service-secrets \
  --from-literal=OPENAI_API_KEY=your-key \
  --from-literal=ANTHROPIC_API_KEY=your-key \
  --from-literal=CIPHER_API_KEY=your-key \
  --from-literal=XAI_API_KEY=your-key \
  -n ai-service
```

### 3. Deploy Qdrant (Vector Database)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
  namespace: ai-service
spec:
  serviceName: qdrant
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        - containerPort: 6334
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
  volumeClaimTemplates:
  - metadata:
      name: qdrant-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: ai-service
spec:
  selector:
    app: qdrant
  ports:
  - port: 6333
    targetPort: 6333
  - port: 6334
    targetPort: 6334
```

### 4. Deploy AI Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-service
  namespace: ai-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-service
  template:
    metadata:
      labels:
        app: ai-service
    spec:
      containers:
      - name: ai-service
        image: woragis/ai-service:1.1.0
        ports:
        - containerPort: 8000
        env:
        - name: VECTOR_DB_TYPE
          value: "qdrant"
        - name: VECTOR_DB_HOST
          value: "qdrant"
        - name: VECTOR_DB_PORT
          value: "6333"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-service-secrets
              key: OPENAI_API_KEY
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-service-secrets
              key: ANTHROPIC_API_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ai-service
  namespace: ai-service
spec:
  selector:
    app: ai-service
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Advanced Deployment Strategies

### Canary Deployment

See `deployment/canary.yaml` for a complete canary deployment configuration.

**Features:**
- Gradual traffic shift (10% → 50% → 100%)
- Automatic rollback on errors
- Health check validation

**Deploy:**
```bash
kubectl apply -f deployment/canary.yaml
```

### Blue-Green Deployment

See `deployment/blue-green.yaml` for a complete blue-green deployment configuration.

**Features:**
- Zero-downtime deployments
- Instant traffic switching
- Easy rollback capability

**Deploy:**
```bash
kubectl apply -f deployment/blue-green.yaml
```

## Configuration Management

### ConfigMaps for Policies

Store policy files in ConfigMaps:

```bash
kubectl create configmap agent-policies \
  --from-file=agents/policies/ \
  -n ai-service

kubectl create configmap routing-policies \
  --from-file=routing/policies/ \
  -n ai-service

kubectl create configmap resilience-policies \
  --from-file=resilience/policies/ \
  -n ai-service
```

Mount in deployment:

```yaml
volumeMounts:
- name: agent-policies
  mountPath: /app/agents/policies
- name: routing-policies
  mountPath: /app/routing/policies
volumes:
- name: agent-policies
  configMap:
    name: agent-policies
```

### Hot Reload

Policies can be reloaded without restarting pods:

```bash
# Update ConfigMap
kubectl create configmap agent-policies \
  --from-file=agents/policies/ \
  --dry-run=client -o yaml | kubectl apply -f -

# Trigger reload in pods
kubectl exec -n ai-service deployment/ai-service -- \
  curl -X POST http://localhost:8000/v1/agents/reload
```

## Monitoring

### Prometheus Integration

The service exposes Prometheus metrics at `/metrics`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-service-metrics
  namespace: ai-service
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: ai-service
  ports:
  - port: 8000
    targetPort: 8000
```

### ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ai-service
  namespace: ai-service
spec:
  selector:
    matchLabels:
      app: ai-service
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

## Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-service-hpa
  namespace: ai-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaling

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: ai-service-vpa
  namespace: ai-service
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-service
  updatePolicy:
    updateMode: "Auto"
```

## Resource Management

### Resource Requests and Limits

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ai-service-pdb
  namespace: ai-service
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: ai-service
```

## Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-service-netpol
  namespace: ai-service
spec:
  podSelector:
    matchLabels:
      app: ai-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: qdrant
    ports:
    - protocol: TCP
      port: 6333
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

## Ingress Configuration

### NGINX Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-service-ingress
  namespace: ai-service
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - ai-service.example.com
    secretName: ai-service-tls
  rules:
  - host: ai-service.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-service
            port:
              number: 80
```

## GitOps Deployment

### ArgoCD

See `gitops/argocd/application.yaml` for ArgoCD configuration.

**Deploy:**
```bash
kubectl apply -f gitops/argocd/application.yaml
```

### Flux

See `gitops/flux/kustomization.yaml` for Flux configuration.

**Deploy:**
```bash
kubectl apply -f gitops/flux/kustomization.yaml
```

## Infrastructure as Code

### Terraform

See `terraform/` directory for Terraform configurations.

**Deploy:**
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n ai-service
kubectl describe pod <pod-name> -n ai-service
```

### View Logs

```bash
kubectl logs -f deployment/ai-service -n ai-service
```

### Check Service Endpoints

```bash
kubectl get endpoints -n ai-service
```

### Port Forward for Local Testing

```bash
kubectl port-forward -n ai-service service/ai-service 8000:80
```

## Best Practices

1. **Use ConfigMaps for Policies**: Enables hot reload without image rebuilds
2. **Set Resource Limits**: Prevents resource exhaustion
3. **Configure Health Checks**: Ensures proper pod lifecycle management
4. **Use HPA**: Automatically scale based on load
5. **Implement PDB**: Maintains availability during disruptions
6. **Monitor Metrics**: Track performance and errors
7. **Use Secrets**: Never hardcode API keys

## Related Documentation

- [Advanced Deployment Strategies](./advanced-deployment.md)
- [GitOps](./gitops.md)
- [Infrastructure as Code](./infrastructure-as-code.md)
- [Monitoring & Alerting](./alerting.md)
- [SLO/SLI Tracking](./slo-sli.md)

