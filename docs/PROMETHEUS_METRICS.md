# Prometheus Metrics

## Overview

The AI service exposes Prometheus metrics for monitoring, alerting, and observability. All metrics are available at `/metrics` endpoint.

## Metrics Endpoint

```
GET /metrics
```

Returns Prometheus-formatted metrics:

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/healthz",status="200"} 1234

# HELP http_request_duration_seconds Request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="POST",path="/v1/chat",le="0.1"} 100
...
```

## Available Metrics

### HTTP Metrics (FastAPI Instrumentator)

Automatically collected by `prometheus-fastapi-instrumentator`:

- **http_requests_total**: Total HTTP requests (counter)
- **http_request_duration_seconds**: Request duration (histogram)
- **http_request_size_bytes**: Request size (histogram)
- **http_response_size_bytes**: Response size (histogram)

### SLO/SLI Metrics

From `app/slo_sli.py`:

- **slo_requests_total**: Total requests by endpoint and status (counter)
- **slo_availability**: Current availability percentage (gauge)
- **slo_latency_seconds**: Request latency (histogram)
- **slo_latency_p95_seconds**: P95 latency (gauge)
- **slo_latency_p99_seconds**: P99 latency (gauge)
- **slo_errors_total**: Total errors by endpoint and type (counter)
- **slo_error_rate**: Current error rate percentage (gauge)
- **slo_error_budget_remaining**: Remaining error budget (gauge)

### Cost Tracking Metrics

From `app/cost_tracking.py`:

- **cost_cpu_usage_cores**: Current CPU usage (gauge)
- **cost_memory_usage_bytes**: Current memory usage (gauge)
- **cost_request_cost_usd**: Estimated cost per request (histogram)
- **cost_total_requests**: Total requests (counter)
- **cost_provider_api_calls_total**: API calls per provider/model (counter)
- **cost_provider_tokens_total**: Tokens per provider/model/type (counter)
- **resource_utilization_percent**: Resource utilization percentage (gauge)

## Metric Types

### Counter

Monotonically increasing value (e.g., total requests):

```
http_requests_total{method="POST",path="/v1/chat",status="200"} 1234
```

### Gauge

Value that can go up or down (e.g., current CPU usage):

```
cost_cpu_usage_cores{pod="ai-service-1",node="node-1"} 0.5
```

### Histogram

Distribution of values (e.g., request duration):

```
http_request_duration_seconds_bucket{method="POST",path="/v1/chat",le="0.1"} 100
http_request_duration_seconds_bucket{method="POST",path="/v1/chat",le="0.5"} 500
http_request_duration_seconds_bucket{method="POST",path="/v1/chat",le="1.0"} 1000
http_request_duration_seconds_sum{method="POST",path="/v1/chat"} 500.0
http_request_duration_seconds_count{method="POST",path="/v1/chat"} 1000
```

## Querying Metrics

### Prometheus Queries

#### Request Rate

```promql
rate(http_requests_total[5m])
```

#### Error Rate

```promql
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

#### P95 Latency

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Cost per Request

```promql
rate(cost_request_cost_usd_sum[5m]) / rate(cost_request_cost_usd_count[5m])
```

#### Provider API Calls

```promql
sum(rate(cost_provider_api_calls_total[5m])) by (provider)
```

## Grafana Dashboards

### Example Dashboard Queries

#### Request Rate by Endpoint

```promql
sum(rate(http_requests_total[5m])) by (path)
```

#### Error Rate by Endpoint

```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) by (path) / 
sum(rate(http_requests_total[5m])) by (path)
```

#### Average Response Time

```promql
rate(http_request_duration_seconds_sum[5m]) / 
rate(http_request_duration_seconds_count[5m])
```

#### Cost by Provider

```promql
sum(rate(cost_request_cost_usd_sum[5m])) by (provider)
```

## Alerting Rules

### High Error Rate

```yaml
- alert: HighErrorRate
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m])) by (path) / 
    sum(rate(http_requests_total[5m])) by (path) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate on {{ $labels.path }}"
```

### High Latency

```yaml
- alert: HighLatency
  expr: |
    histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "P95 latency exceeds 1 second"
```

### Budget Exceeded

```yaml
- alert: BudgetExceeded
  expr: |
    sum(rate(cost_request_cost_usd_sum[1h])) > 10
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "Hourly cost exceeds $10"
```

## Configuration

### Prometheus Scraping

Configure Prometheus to scrape the service:

```yaml
scrape_configs:
  - job_name: 'ai-service'
    scrape_interval: 30s
    static_configs:
      - targets: ['ai-service:8000']
    metrics_path: '/metrics'
```

### ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ai-service
spec:
  selector:
    matchLabels:
      app: ai-service
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

## Best Practices

1. **Use Appropriate Metric Types** - Counter for totals, Gauge for current values, Histogram for distributions
2. **Label Consistently** - Use consistent label names across metrics
3. **Avoid High Cardinality** - Don't use high-cardinality labels (e.g., user IDs)
4. **Set Appropriate Buckets** - Configure histogram buckets for your use case
5. **Monitor Metric Volume** - Too many metrics can impact performance

## Custom Metrics

### Adding Custom Metrics

```python
from prometheus_client import Counter, Gauge, Histogram

# Counter
custom_events_total = Counter(
    'custom_events_total',
    'Total custom events',
    ['event_type']
)

# Gauge
custom_value = Gauge(
    'custom_value',
    'Current custom value',
    ['label']
)

# Histogram
custom_duration = Histogram(
    'custom_duration_seconds',
    'Custom operation duration',
    ['operation'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0]
)

# Usage
custom_events_total.labels(event_type='test').inc()
custom_value.labels(label='test').set(42)
custom_duration.labels(operation='test').observe(0.5)
```

## Related Documentation

- [SLO/SLI Tracking](./slo-sli.md)
- [Alerting](./alerting.md)
- [Cost Tracking](./cost-optimization.md)
- [Kubernetes Deployment](./KUBERNETES_DEPLOYMENT.md)

