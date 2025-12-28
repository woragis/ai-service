# Cost Optimization Guide

This guide explains cost tracking and optimization for AI Service.

## Overview

Cost tracking helps identify optimization opportunities by monitoring:
- Resource usage (CPU, memory)
- Request costs
- Provider API usage
- Token consumption

## Implementation

**Location:** `app/cost_tracking.py`

**Metrics Exposed:**
- `cost_cpu_usage_cores` - CPU usage
- `cost_memory_usage_bytes` - Memory usage
- `cost_request_cost_usd` - Cost per request
- `cost_provider_api_calls_total` - API call count
- `cost_provider_tokens_total` - Token usage

## Cost Estimation

Costs are estimated based on:
- Provider pricing (OpenAI, Anthropic, etc.)
- Token usage (input/output)
- Request volume

**Example Pricing:**
- OpenAI GPT-4o-mini: $0.15/$0.60 per 1M tokens (input/output)
- Anthropic Claude: $3.00/$15.00 per 1M tokens (input/output)

## Usage

### Track Request Cost

```python
from app.cost_tracking import cost_tracker

# Record request
cost_tracker.record_request(
    endpoint="/v1/chat",
    provider="openai",
    cost_usd=0.001
)
```

### Track API Calls

```python
cost_tracker.record_api_call("openai", "gpt-4o-mini")
```

### Track Tokens

```python
cost_tracker.record_tokens(
    provider="openai",
    model="gpt-4o-mini",
    input_tokens=100,
    output_tokens=50
)
```

## Cost Analysis

### Prometheus Queries

**Total Cost:**
```promql
sum(rate(cost_request_cost_usd_sum[1h]))
```

**Cost per Endpoint:**
```promql
sum(rate(cost_request_cost_usd_sum[1h])) by (endpoint)
```

**Provider Costs:**
```promql
sum(rate(cost_provider_tokens_total[1h])) by (provider, model)
```

**Resource Costs:**
```promql
avg(cost_cpu_usage_cores) * cpu_cost_per_core
avg(cost_memory_usage_bytes) / 1024 / 1024 / 1024 * memory_cost_per_gb
```

## Optimization Strategies

### 1. Right-Size Resources

- Review CPU/memory usage
- Adjust resource requests/limits
- Use HPA for auto-scaling

### 2. Optimize Provider Usage

- Use cheaper models when possible
- Cache responses
- Batch requests
- Monitor token usage

### 3. Reduce Request Volume

- Implement caching
- Use CDN for static content
- Optimize API calls
- Rate limiting

### 4. Monitor Trends

- Track cost over time
- Identify cost spikes
- Review expensive endpoints
- Optimize high-cost operations

## Cost Dashboards

Create Grafana dashboards for:
- Total cost per day/week/month
- Cost per endpoint
- Cost per provider
- Resource utilization
- Cost trends

## Best Practices

1. **Track Continuously**: Monitor costs regularly
2. **Set Budgets**: Define cost budgets
3. **Alert on Spikes**: Alert when costs exceed thresholds
4. **Review Regularly**: Weekly/monthly cost reviews
5. **Optimize Proactively**: Don't wait for problems

## Troubleshooting

### High Costs

1. Check request volume
2. Review provider usage
3. Check resource utilization
4. Review expensive endpoints
5. Consider caching

### Missing Metrics

1. Verify cost tracking is enabled
2. Check Prometheus scraping
3. Review metric names
4. Check for errors in logs

