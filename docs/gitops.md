# GitOps Guide

This guide explains GitOps implementation for AI Service using ArgoCD or Flux.

## Overview

GitOps automates deployment by syncing Kubernetes manifests from Git to your cluster. Changes to Git automatically trigger deployments.

## ArgoCD

**Location:** `gitops/argocd/application.yaml`

### Features

- Web UI for visualization
- Automated sync
- Self-healing
- Pruning
- Revision history

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

3. Access UI:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# https://localhost:8080
```

### Configuration

Edit `gitops/argocd/application.yaml`:
- `repoURL`: Your Git repository
- `targetRevision`: Branch or tag
- `path`: Path to Kubernetes manifests

## Flux

**Location:** `gitops/flux/kustomization.yaml`

### Features

- CLI-based
- Automated sync
- Pruning
- GitRepository source

### Setup

1. Install Flux:
```bash
flux install
```

2. Apply configuration:
```bash
kubectl apply -f gitops/flux/kustomization.yaml
```

3. Check status:
```bash
flux get kustomizations
```

### Configuration

Edit `gitops/flux/kustomization.yaml`:
- `interval`: Sync interval (default: 5m)
- `path`: Path to manifests
- `url`: Git repository URL

## Workflow

1. **Make Changes**: Update Kubernetes manifests in Git
2. **Commit & Push**: Push changes to repository
3. **Auto Sync**: ArgoCD/Flux detects changes
4. **Deploy**: Automatically applies to cluster
5. **Monitor**: Monitor deployment status

## Best Practices

1. **Use Separate Branches**: `main` for prod, `develop` for staging
2. **Review Changes**: Review PRs before merging
3. **Test First**: Test in staging before production
4. **Monitor Sync**: Monitor sync status regularly
5. **Rollback Plan**: Have rollback strategy ready

## Troubleshooting

### Sync Failures

1. Check Git repository access
2. Verify manifest validity
3. Check cluster permissions
4. Review sync logs

### Drift Detection

1. Check for manual changes
2. Review sync status
3. Use self-healing (ArgoCD)
4. Reconcile manually (Flux)

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Flux Documentation](https://fluxcd.io/docs/)

