# Feature Deployment Guide

This document explains where each feature runs and how it's deployed.

## Feature Locations

### ✅ Runtime Features (In Docker Image)

These features are **included in the Docker image** and work when the container runs:

#### 1. SLO/SLI Tracking
- **Location**: `app/slo_sli.py`, `app/middleware_slo.py`
- **In Docker**: ✅ Yes (part of `app/` directory)
- **How it works**: 
  - Runs inside the container
  - Tracks request metrics automatically
  - Exposes metrics at `/metrics` endpoint
- **Usage**: Works automatically when service runs
- **Portable**: ✅ Yes, works in any Docker environment

### ❌ CI/CD Features (Not in Docker Image)

These features run **during CI/CD**, not in the Docker image:

#### 1. Performance Testing
- **Location**: `tests/performance/`
- **In Docker**: ❌ No (not copied to image)
- **How it works**: 
  - Runs in GitHub Actions CI/CD
  - Tests the service before deployment
  - Not included in production image
- **Usage**: Run in CI/CD or locally for testing
- **Portable**: ❌ No, specific to this repository's CI/CD

#### 2. Security Testing
- **Location**: `.github/workflows/ci.yml` (security-tests job)
- **In Docker**: ❌ No
- **How it works**: 
  - Runs in GitHub Actions CI/CD
  - Scans code and dependencies
  - Not included in production image
- **Usage**: Automatic in CI/CD pipeline
- **Portable**: ❌ No, specific to this repository's CI/CD

### ❌ Infrastructure Features (Separate from Docker)

These features are **configuration files** for infrastructure, not part of the Docker image:

#### 1. Alerting Rules
- **Location**: `monitoring/alerts.yml`
- **In Docker**: ❌ No
- **How it works**: 
  - Prometheus reads this file separately
  - Not included in Docker image
  - Deployed to Prometheus server
- **Usage**: Copy to Prometheus server configuration
- **Portable**: ✅ Yes, can be used with any Prometheus setup

#### 2. Deployment Configurations
- **Location**: `deployment/canary.yaml`, `deployment/blue-green.yaml`
- **In Docker**: ❌ No
- **How it works**: 
  - Kubernetes manifests, not Docker image content
  - Applied to Kubernetes cluster separately
  - Reference the Docker image (e.g., `woragis/ai-service:v1.1.0`)
- **Usage**: Apply to Kubernetes cluster with `kubectl apply`
- **Portable**: ✅ Yes, can be used with any Kubernetes cluster

## What's Actually in the Docker Image

The Dockerfile only copies:
```dockerfile
COPY requirements.txt /app/requirements.txt
COPY app /app/app
```

**Included in image:**
- ✅ Application code (`app/`)
- ✅ SLO/SLI tracking code
- ✅ All Python dependencies
- ✅ Metrics endpoint (`/metrics`)

**NOT included in image:**
- ❌ Tests (`tests/`)
- ❌ Documentation (`docs/`)
- ❌ Monitoring configs (`monitoring/`)
- ❌ Deployment configs (`deployment/`)
- ❌ CI/CD workflows (`.github/`)

## Using Features in Other Services

### ✅ Portable Features (Can be reused)

1. **SLO/SLI Code** - Copy `app/slo_sli.py` and `app/middleware_slo.py` to other services
2. **Alerting Rules** - Adapt `monitoring/alerts.yml` for other services
3. **Deployment Configs** - Adapt `deployment/*.yaml` for other services

### ❌ Service-Specific Features

1. **CI/CD Workflows** - Each service has its own `.github/workflows/`
2. **Tests** - Each service has its own test suite
3. **Documentation** - Service-specific

## Deployment Scenarios

### Scenario 1: Using Docker Image Directly

If you pull and run the Docker image:
```bash
docker run -p 8000:8000 woragis/ai-service:v1.1.0
```

**What works:**
- ✅ Service runs
- ✅ SLO/SLI metrics exposed at `/metrics`
- ✅ Health check at `/healthz`

**What doesn't work:**
- ❌ Alerting (needs Prometheus + alert rules)
- ❌ Performance tests (not in image)
- ❌ Security tests (not in image)

### Scenario 2: Kubernetes Deployment

If you deploy using Kubernetes:
```bash
kubectl apply -f deployment/canary.yaml
```

**What works:**
- ✅ Service runs in Kubernetes
- ✅ Canary deployment strategy
- ✅ SLO/SLI metrics (if Prometheus is configured)
- ✅ Alerting (if Prometheus + alert rules are deployed)

**What doesn't work:**
- ❌ Performance tests (run in CI/CD, not in cluster)
- ❌ Security tests (run in CI/CD, not in cluster)

### Scenario 3: Using in Another Service

To use SLO/SLI tracking in another service:

1. **Copy the code:**
   ```bash
   cp app/slo_sli.py <other-service>/app/
   cp app/middleware_slo.py <other-service>/app/
   ```

2. **Add to requirements.txt:**
   ```txt
   prometheus-client==0.21.0
   ```

3. **Integrate middleware:**
   ```python
   from app.middleware_slo import SLOTrackingMiddleware
   app.add_middleware(SLOTrackingMiddleware)
   ```

4. **Adapt alerting rules:**
   - Copy `monitoring/alerts.yml`
   - Update service name and metrics
   - Deploy to Prometheus

## Best Practices

1. **Runtime Features**: Include in Docker image (SLO/SLI)
2. **CI/CD Features**: Keep in repository, run in CI/CD
3. **Infrastructure Configs**: Deploy separately to infrastructure
4. **Documentation**: Keep in repository for reference

## Summary

| Feature | In Docker Image | Works in Container | Portable to Other Services |
|---------|----------------|-------------------|---------------------------|
| SLO/SLI Tracking | ✅ Yes | ✅ Yes | ✅ Yes |
| Performance Tests | ❌ No | ❌ No | ⚠️ Adaptable |
| Security Tests | ❌ No | ❌ No | ⚠️ Adaptable |
| Alerting Rules | ❌ No | ❌ No | ✅ Yes |
| Deployment Configs | ❌ No | ❌ No | ✅ Yes |

**Key Point**: Only runtime code (in `app/`) is in the Docker image. Everything else is for CI/CD or infrastructure configuration.

