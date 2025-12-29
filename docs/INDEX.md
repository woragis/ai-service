# AI Service Documentation Index

## Getting Started

- [README](./README.md) - Overview and quick start guide
- [Testing Locally](./TESTING-LOCAL.md) - How to test the service locally
- [Feature Deployment](./FEATURE_DEPLOYMENT.md) - How to deploy new features

## Core Features

### Agent System
- [Agent Policies](./AGENT_POLICIES.md) - YAML-based agent configuration
- [Agent Policy Architecture](./AGENT_POLICY_ARCHITECTURE.md) - Technical architecture of agent system
- [Agent Auto-Selection](./AGENT_AUTO_SELECTION.md) - Automatic agent selection based on query content

### Knowledge Base & RAG
- [Vector DB Options](./VECTOR_DB_OPTIONS.md) - Supported vector databases and configuration
- [RAG Implementation](./VECTOR_DB_OPTIONS.md) - Retrieval-Augmented Generation setup

### LLM Providers
- [LLM Providers](./LLM_PROVIDERS.md) - Supported providers (OpenAI, Anthropic, xAI, Cipher, Manus)
- [Image Generation](./IMAGE_GENERATION.md) - Image generation with Cipher provider
- [Streaming Chat](./STREAMING_CHAT.md) - Real-time streaming chat responses

### Logging & Observability
- [Structured Logging](./STRUCTURED_LOGGING.md) - JSON/text logging with trace IDs
- [Prometheus Metrics](./PROMETHEUS_METRICS.md) - Metrics collection and monitoring
- [Health Checks](./HEALTH_CHECKS.md) - Health check endpoints and monitoring

### Extensibility
- [Plugin System](./PLUGIN_SYSTEM.md) - Custom vector DB and file storage plugins
- [CORS Configuration](./CORS_CONFIGURATION.md) - Cross-Origin Resource Sharing setup
- [Request Overrides](./REQUEST_OVERRIDES.md) - Per-request model and temperature overrides

## Policy Systems

### 1. Model Selection & Routing
- [Routing Policies](./ROUTING_POLICIES.md) - Provider selection, fallback chains, complexity detection
- [Model Selection & Routing Policies](./ROUTING_POLICIES.md) - Cost vs quality trade-offs

### 2. Retry & Resilience
- [Retry & Resilience Policies](./RETRY_RESILIENCE.md) - Retry strategies, timeouts, graceful degradation
- [Circuit Breakers](./CIRCUIT_BREAKERS.md) - Circuit breaker pattern implementation

### 3. Cost Control
- [Cost Control Policies](./COST_CONTROL.md) - Budget limits, token limits, cost-based routing
- [Cost Optimization](./cost-optimization.md) - Cost optimization strategies

### 4. Caching
- [Caching Policies](./CACHING_POLICIES.md) - In-memory caching, semantic similarity caching, TTL configuration

### 5. Security & Content
- [Security & Content Policies](./SECURITY_POLICIES.md) - Content filtering, PII detection, prompt injection detection
- [Security Testing](./security-testing.md) - Security testing with Bandit, Safety, pip-audit

### 6. Quality & Validation
- [Quality & Validation Policies](./QUALITY_POLICIES.md) - Length limits, format validation, quality checks, toxicity detection

### 7. Feature Flags
- [Feature Flag Policies](./FEATURE_FLAGS.md) - RAG enable/disable, streaming control, provider management

## Deployment & Infrastructure

### Kubernetes
- [Kubernetes Deployment](./KUBERNETES_DEPLOYMENT.md) - Complete Kubernetes deployment guide
- [Advanced Deployment Strategies](./advanced-deployment.md) - Canary, blue-green deployments
- [GitOps](./gitops.md) - ArgoCD and Flux configurations
- [Infrastructure as Code](./infrastructure-as-code.md) - Terraform configurations

### Docker
- [Docker Configuration](./TESTING-LOCAL.md) - Docker setup and testing
- [Docker Compose](./TESTING-LOCAL.md) - Local development with docker-compose

## Monitoring & Observability

### Metrics & Alerting
- [SLO/SLI Tracking](./slo-sli.md) - Service Level Objectives and Indicators
- [Alerting](./alerting.md) - Prometheus alerting rules and configuration
- [Monitoring Setup](./alerting.md) - Prometheus and Grafana setup

### Tracing & Logging
- [Distributed Tracing](./distributed-tracing.md) - OpenTelemetry integration
- [Request Timeouts](./request-timeouts.md) - Timeout configuration and handling
- [Graceful Shutdown](./graceful-shutdown.md) - Clean shutdown handling

## Testing

### Test Types
- [Performance Testing](./performance-testing.md) - Load, stress, spike tests
- [Security Testing](./security-testing.md) - SAST, dependency scanning
- [Chaos Engineering](./chaos-engineering.md) - Failure simulation tests
- [Contract Testing](./contract-testing.md) - Pact-based API contract tests

### CI/CD
- [CI/CD Features](./CI-CD-FEATURES.md) - GitHub Actions workflows and automation

## Implementation Details

- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md) - Overview of all implemented features
- [Pleno Features](./pleno-features.md) - Features implemented for Pleno level requirements

## Quick Reference

### API Endpoints

#### Core Endpoints
- `POST /v1/chat` - Chat completion
- `POST /v1/chat/stream` - Streaming chat
- `POST /v1/images` - Image generation
- `GET /healthz` - Health check

#### Policy Management
- `POST /v1/agents/reload` - Reload agent policies
- `POST /v1/routing/reload` - Reload routing policies
- `POST /v1/resilience/reload` - Reload resilience policies
- `POST /v1/cost/reload` - Reload cost control policies
- `POST /v1/cache/reload` - Reload caching policies
- `POST /v1/security/reload` - Reload security policies
- `POST /v1/quality/reload` - Reload quality policies
- `POST /v1/features/reload` - Reload feature flags

#### Configuration Endpoints
- `GET /v1/cost/budget` - Budget status
- `GET /v1/cost/token-limits` - Token limits
- `GET /v1/cache/stats` - Cache statistics
- `GET /v1/quality/length-limits` - Length limits
- `GET /v1/features/config` - Feature flags config

### Policy Files

All policies are YAML files in their respective directories:

- `agents/policies/*.yaml` - Agent definitions
- `routing/policies/routing.yaml` - Routing configuration
- `resilience/policies/resilience.yaml` - Resilience configuration
- `cost_control/policies/cost_control.yaml` - Cost control configuration
- `caching/policies/caching.yaml` - Caching configuration
- `security/policies/security.yaml` - Security configuration
- `quality/policies/quality.yaml` - Quality configuration
- `features/policies/features.yaml` - Feature flags

### Environment Variables

Key environment variables:

- `VECTOR_DB_TYPE` - Vector database type (qdrant, chroma, etc.)
- `VECTOR_DB_HOST` - Vector database host
- `FILE_STORAGE_TYPE` - File storage type (local, s3, etc.)
- `COST_MODE` - Cost mode (cost_optimized, balanced, quality_optimized)
- `AGENT_POLICIES_PATH` - Path to agent policies
- `ROUTING_POLICIES_PATH` - Path to routing policies
- `RESILIENCE_POLICIES_PATH` - Path to resilience policies
- `COST_CONTROL_POLICIES_PATH` - Path to cost control policies
- `CACHING_POLICIES_PATH` - Path to caching policies
- `SECURITY_POLICIES_PATH` - Path to security policies
- `QUALITY_POLICIES_PATH` - Path to quality policies
- `FEATURE_POLICIES_PATH` - Path to feature flags

## Documentation by Category

### For Developers
- [Agent Policies](./AGENT_POLICIES.md)
- [Testing Locally](./TESTING-LOCAL.md)
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- [CI/CD Features](./CI-CD-FEATURES.md)

### For DevOps
- [Kubernetes Deployment](./KUBERNETES_DEPLOYMENT.md)
- [Advanced Deployment](./advanced-deployment.md)
- [GitOps](./gitops.md)
- [Infrastructure as Code](./infrastructure-as-code.md)
- [Monitoring & Alerting](./alerting.md)

### For Security
- [Security & Content Policies](./SECURITY_POLICIES.md)
- [Security Testing](./security-testing.md)
- [Distributed Tracing](./distributed-tracing.md)

### For Operations
- [SLO/SLI Tracking](./slo-sli.md)
- [Performance Testing](./performance-testing.md)
- [Cost Optimization](./cost-optimization.md)
- [Graceful Shutdown](./graceful-shutdown.md)

### For Architects
- [Agent Policy Architecture](./AGENT_POLICY_ARCHITECTURE.md)
- [Circuit Breakers](./CIRCUIT_BREAKERS.md)
- [Retry & Resilience](./RETRY_RESILIENCE.md)
- [Routing Policies](./ROUTING_POLICIES.md)

## Feature Matrix

| Feature | Status | Documentation |
|---------|--------|---------------|
| Multi-Provider LLM | ✅ | [LLM Providers](./LLM_PROVIDERS.md), [Routing Policies](./ROUTING_POLICIES.md) |
| Agent System | ✅ | [Agent Policies](./AGENT_POLICIES.md), [Agent Auto-Selection](./AGENT_AUTO_SELECTION.md) |
| RAG | ✅ | [Vector DB Options](./VECTOR_DB_OPTIONS.md) |
| Image Generation | ✅ | [Image Generation](./IMAGE_GENERATION.md) |
| Streaming Chat | ✅ | [Streaming Chat](./STREAMING_CHAT.md) |
| Circuit Breakers | ✅ | [Circuit Breakers](./CIRCUIT_BREAKERS.md) |
| Retry Strategies | ✅ | [Retry & Resilience](./RETRY_RESILIENCE.md) |
| Cost Control | ✅ | [Cost Control](./COST_CONTROL.md) |
| Caching | ✅ | [Caching Policies](./CACHING_POLICIES.md) |
| Security | ✅ | [Security Policies](./SECURITY_POLICIES.md) |
| Quality Checks | ✅ | [Quality Policies](./QUALITY_POLICIES.md) |
| Feature Flags | ✅ | [Feature Flags](./FEATURE_FLAGS.md) |
| Structured Logging | ✅ | [Structured Logging](./STRUCTURED_LOGGING.md) |
| Prometheus Metrics | ✅ | [Prometheus Metrics](./PROMETHEUS_METRICS.md) |
| Health Checks | ✅ | [Health Checks](./HEALTH_CHECKS.md) |
| Plugin System | ✅ | [Plugin System](./PLUGIN_SYSTEM.md) |
| CORS Support | ✅ | [CORS Configuration](./CORS_CONFIGURATION.md) |
| Request Overrides | ✅ | [Request Overrides](./REQUEST_OVERRIDES.md) |
| Kubernetes | ✅ | [Kubernetes Deployment](./KUBERNETES_DEPLOYMENT.md) |
| Monitoring | ✅ | [SLO/SLI](./slo-sli.md), [Alerting](./alerting.md) |
| Tracing | ✅ | [Distributed Tracing](./distributed-tracing.md) |

## Getting Help

1. Check the relevant documentation section above
2. Review [Implementation Summary](./IMPLEMENTATION_SUMMARY.md) for feature overview
3. See [Testing Locally](./TESTING-LOCAL.md) for local setup
4. Check [CI/CD Features](./CI-CD-FEATURES.md) for automated testing

## Contributing

When adding new features:
1. Update relevant policy documentation
2. Add to this index
3. Update [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
4. Add tests and update [CI/CD Features](./CI-CD-FEATURES.md)

