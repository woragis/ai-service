# CI/CD Features Overview

This document explains which features run in CI/CD vs. what goes into the Docker image.

## Features in CI/CD

The following features run **during CI/CD** (not in Docker image):

### ✅ Unit Tests
- **Location**: `tests/unit/`
- **Runs in**: `unit-tests` job
- **Purpose**: Test individual components

### ✅ Integration Tests
- **Location**: `tests/integration/`
- **Runs in**: `integration-tests` job
- **Purpose**: Test API endpoints with real providers

### ✅ Security Tests
- **Tools**: Bandit, Safety, pip-audit
- **Runs in**: `security-tests` job
- **Purpose**: Scan for vulnerabilities

### ✅ Performance Tests
- **Location**: `tests/performance/`
- **Runs in**: `performance-tests` job
- **Purpose**: Load, stress, spike tests

### ✅ Chaos Engineering Tests
- **Location**: `tests/chaos/`
- **Runs in**: `chaos-tests` job
- **Purpose**: Test resilience under failure

### ✅ Contract Tests
- **Location**: `tests/contract/`
- **Runs in**: `contract-tests` job
- **Purpose**: Verify API contracts with Pact

### ✅ Docker Build
- **Runs in**: `docker-build` job
- **Purpose**: Build and validate Docker image

## Features in Docker Image

The following features are **included in the Docker image** (runtime features):

### ✅ Request Timeouts
- **Location**: `app/middleware_timeout.py`
- **In Docker**: ✅ Yes (part of `app/`)
- **Works**: Automatically enforces timeouts

### ✅ Graceful Shutdown
- **Location**: `app/graceful_shutdown.py`
- **In Docker**: ✅ Yes (part of `app/`)
- **Works**: Handles SIGTERM/SIGINT

### ✅ Distributed Tracing
- **Location**: `app/tracing.py`
- **In Docker**: ✅ Yes (part of `app/`)
- **Works**: OpenTelemetry instrumentation

### ✅ SLO/SLI Tracking
- **Location**: `app/slo_sli.py`, `app/middleware_slo.py`
- **In Docker**: ✅ Yes (part of `app/`)
- **Works**: Exposes metrics at `/metrics`

### ✅ Cost Tracking
- **Location**: `app/cost_tracking.py`
- **In Docker**: ✅ Yes (part of `app/`)
- **Works**: Tracks costs and exposes metrics

## Features NOT in Docker Image

The following are **configuration/infrastructure** (not in Docker):

### ❌ GitOps Configs
- **Location**: `gitops/argocd/`, `gitops/flux/`
- **In Docker**: ❌ No
- **Usage**: Deploy separately to cluster

### ❌ Terraform Configs
- **Location**: `terraform/`
- **In Docker**: ❌ No
- **Usage**: Deploy infrastructure separately

### ❌ Alerting Rules
- **Location**: `monitoring/alerts.yml`
- **In Docker**: ❌ No
- **Usage**: Deploy to Prometheus

### ❌ Tests
- **Location**: `tests/`
- **In Docker**: ❌ No
- **Usage**: Run in CI/CD or locally

## Summary Table

| Feature | In CI/CD | In Docker Image | Type |
|---------|----------|----------------|------|
| Unit Tests | ✅ | ❌ | CI/CD |
| Integration Tests | ✅ | ❌ | CI/CD |
| Security Tests | ✅ | ❌ | CI/CD |
| Performance Tests | ✅ | ❌ | CI/CD |
| Chaos Tests | ✅ | ❌ | CI/CD |
| Contract Tests | ✅ | ❌ | CI/CD |
| Request Timeouts | ❌ | ✅ | Runtime |
| Graceful Shutdown | ❌ | ✅ | Runtime |
| Distributed Tracing | ❌ | ✅ | Runtime |
| SLO/SLI Tracking | ❌ | ✅ | Runtime |
| Cost Tracking | ❌ | ✅ | Runtime |
| GitOps Configs | ❌ | ❌ | Infrastructure |
| Terraform Configs | ❌ | ❌ | Infrastructure |
| Alerting Rules | ❌ | ❌ | Infrastructure |

## Docker Image Contents

The Dockerfile only copies:
```dockerfile
COPY requirements.txt /app/requirements.txt
COPY app /app/app
```

**Included:**
- ✅ All runtime code (`app/`)
- ✅ Request timeouts
- ✅ Graceful shutdown
- ✅ Distributed tracing
- ✅ SLO/SLI tracking
- ✅ Cost tracking

**NOT Included:**
- ❌ Tests (`tests/`)
- ❌ Documentation (`docs/`)
- ❌ GitOps (`gitops/`)
- ❌ Terraform (`terraform/`)
- ❌ Monitoring configs (`monitoring/`)

