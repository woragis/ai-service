# SLO/SLI Tracking Guide

This guide explains Service Level Objectives (SLOs) and Service Level Indicators (SLIs) for the AI Service.

## Overview

SLOs define the reliability and performance targets for the service. SLIs are the metrics used to measure whether we're meeting those targets.

## SLO Targets

The AI Service has the following SLO targets:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Availability | 99.9% | Percentage of successful requests |
| Latency P95 | < 500ms | 95th percentile request latency |
| Latency P99 | < 1000ms | 99th percentile request latency |
| Error Rate | < 0.1% | Percentage of failed requests |

## Implementation

SLO/SLI tracking is implemented in `app/slo_sli.py` and automatically tracks metrics via `app/middleware_slo.py`.

### Metrics Exposed

The following Prometheus metrics are exposed:

- `slo_requests_total` - Total requests by endpoint and status
- `slo_availability` - Current availability percentage
- `slo_latency_histogram` - Request latency histogram
- `slo_latency_p95` - P95 latency
- `slo_latency_p99` - P99 latency
- `slo_errors_total` - Total errors by endpoint and type
- `slo_error_rate` - Current error rate percentage
- `slo_error_budget_remaining` - Remaining error budget

### Usage

SLO tracking is automatic for all requests. The middleware records:
- Request endpoint
- HTTP status code
- Request duration

Example:
```python
from app.slo_sli import slo_tracker

# Check SLO compliance
compliance = slo_tracker.check_slo_compliance('/v1/chat')
print(compliance)
```

## Error Budget

Error budget is the amount of errors allowed while still meeting SLO targets.

**Error Budget Calculation:**
```
Error Budget = (1 - Availability Target) × Time Window
```

For 99.9% availability over 30 days:
```
Error Budget = 0.1% × 30 days = 0.03 days = 43.2 minutes
```

This means we can have up to 43.2 minutes of downtime per month while still meeting our SLO.

## Monitoring SLOs

### Prometheus Queries

**Availability:**
```promql
(
  sum(rate(slo_requests_total{status="success"}[5m])) by (endpoint)
  /
  sum(rate(slo_requests_total[5m])) by (endpoint)
) * 100
```

**Error Rate:**
```promql
(
  sum(rate(slo_errors_total[5m])) by (endpoint)
  /
  sum(rate(slo_requests_total[5m])) by (endpoint)
) * 100
```

**P95 Latency:**
```promql
histogram_quantile(0.95,
  sum(rate(slo_latency_histogram_bucket[5m])) by (le, endpoint)
)
```

**Error Budget Remaining:**
```promql
slo_error_budget_remaining
```

### Grafana Dashboard

Create a Grafana dashboard with panels for:
1. Availability percentage (gauge)
2. Error rate (graph)
3. P95/P99 latency (graph)
4. Error budget remaining (gauge)
5. SLO compliance status (stat panel)

## SLO Compliance

Check SLO compliance programmatically:

```python
from app.slo_sli import slo_tracker

compliance = slo_tracker.check_slo_compliance('/v1/chat')
if not compliance['overall_compliant']:
    # Take action: alert, scale, etc.
    pass
```

## Alerting on SLO Violations

Alerts are configured in `monitoring/alerts.yml`:
- `LowAvailability` - Triggers when availability < 99.9%
- `ErrorBudgetDepletion` - Triggers when error budget is being depleted

## Best Practices

1. **Set Realistic Targets**: SLOs should be achievable but challenging
2. **Measure Continuously**: Track SLIs in real-time
3. **Review Regularly**: Review SLO compliance weekly/monthly
4. **Adjust as Needed**: Update SLOs based on business needs
5. **Communicate**: Share SLO status with stakeholders
6. **Error Budget**: Use error budget to make deployment decisions

## Troubleshooting

### SLO Metrics Not Appearing

1. Check middleware is enabled: `app.add_middleware(SLOTrackingMiddleware)`
2. Check Prometheus is scraping: `curl http://ai-service:8080/metrics | grep slo_`
3. Check metrics are being recorded: Look for `slo_requests_total` in metrics

### SLO Compliance Issues

1. Check error rate: High error rate affects availability
2. Check latency: High latency may indicate performance issues
3. Check external dependencies: API failures affect SLOs
4. Review recent changes: Deployments may have introduced issues

## References

- [Google SRE Book - SLOs](https://sre.google/sre-book/service-level-objectives/)
- [Prometheus SLO Examples](https://prometheus.io/docs/practices/alerting/)

