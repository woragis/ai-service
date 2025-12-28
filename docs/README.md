# AI Service Documentation

This directory contains comprehensive documentation for the AI Service, covering advanced features and operational procedures.

## Documentation Index

### Senior-Level Features
1. [Alerting Guide](./alerting.md) - Prometheus alerting configuration and management
2. [SLO/SLI Tracking](./slo-sli.md) - Service Level Objectives and Indicators
3. [Performance Testing](./performance-testing.md) - Load, stress, and spike testing
4. [Security Testing](./security-testing.md) - SAST, DAST, and dependency scanning
5. [Advanced Deployment](./advanced-deployment.md) - Canary and blue-green deployments
6. [Feature Deployment](./FEATURE_DEPLOYMENT.md) - Where features run and how to deploy them

### Pleno-Level Features
7. [Request Timeouts](./request-timeouts.md) - Per-request timeout configuration
8. [Graceful Shutdown](./graceful-shutdown.md) - Clean shutdown handling
9. [Distributed Tracing](./distributed-tracing.md) - OpenTelemetry tracing implementation
10. [Cost Optimization](./cost-optimization.md) - Cost tracking and optimization
11. [Chaos Engineering](./chaos-engineering.md) - Failure scenario testing
12. [Contract Testing](./contract-testing.md) - API contract verification with Pact
13. [GitOps](./gitops.md) - Automated deployment with ArgoCD/Flux
14. [Infrastructure as Code](./infrastructure-as-code.md) - Terraform configuration
15. [Pleno Features Summary](./pleno-features.md) - Overview of all Pleno-level features

## Quick Links

- **Monitoring**: Prometheus metrics at `/metrics`
- **Health Checks**: `/healthz`
- **API Documentation**: See main README
- **Deployment Configs**: `deployment/` directory

## Getting Started

1. Read the [Alerting Guide](./alerting.md) to set up monitoring alerts
2. Review [SLO/SLI Tracking](./slo-sli.md) to understand service objectives
3. Run [Performance Tests](./performance-testing.md) to establish baselines
4. Set up [Security Testing](./security-testing.md) in CI/CD
5. Use [Advanced Deployment](./advanced-deployment.md) strategies for production

