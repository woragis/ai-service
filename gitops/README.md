# GitOps Configuration

This directory contains GitOps configurations for automated deployment using ArgoCD or Flux.

## ArgoCD

**Location:** `gitops/argocd/application.yaml`

ArgoCD automatically syncs Kubernetes manifests from Git to your cluster.

### Setup

1. Install ArgoCD:
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

2. Apply application:
```bash
kubectl apply -f gitops/argocd/application.yaml
```

3. Access ArgoCD UI:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080
# Default username: admin
# Get password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### Features

- **Automated Sync**: Automatically syncs changes from Git
- **Self-Healing**: Automatically corrects drift
- **Pruning**: Removes resources deleted from Git
- **Revision History**: Keeps last 10 revisions

## Flux

**Location:** `gitops/flux/kustomization.yaml`

Flux automatically syncs Kubernetes manifests from Git to your cluster.

### Setup

1. Install Flux:
```bash
flux install
```

2. Create GitRepository:
```bash
kubectl apply -f gitops/flux/kustomization.yaml
```

3. Check sync status:
```bash
flux get kustomizations
```

### Features

- **Automated Sync**: Syncs every 5 minutes
- **Pruning**: Removes resources deleted from Git
- **Timeout**: 5 minute sync timeout
- **Namespace**: Deploys to default namespace

## Comparison

| Feature | ArgoCD | Flux |
|---------|--------|------|
| UI | ✅ Web UI | ❌ CLI only |
| Sync Interval | Configurable | 5 minutes |
| Self-Healing | ✅ Yes | ⚠️ Manual |
| Pruning | ✅ Yes | ✅ Yes |
| Complexity | Medium | Low |

## Best Practices

1. **Use Separate Branches**: Use `main` for production, `develop` for staging
2. **Review Changes**: Review PRs before merging to main
3. **Monitor Sync**: Monitor sync status regularly
4. **Test First**: Test in staging before production
5. **Rollback Plan**: Have a rollback strategy ready

## Troubleshooting

### ArgoCD Sync Issues

```bash
# Check application status
kubectl get application ai-service -n argocd

# Check sync status
argocd app get ai-service

# Force sync
argocd app sync ai-service
```

### Flux Sync Issues

```bash
# Check kustomization status
flux get kustomizations ai-service

# Check git repository
flux get sources git ai-service

# Reconcile manually
flux reconcile kustomization ai-service
```

