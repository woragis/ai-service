# Cost Control Policies

## Overview

The AI service implements comprehensive cost control mechanisms to manage spending, enforce budgets, and optimize costs through intelligent routing.

## Features

### 1. Budget Limits

Track and enforce spending limits at multiple levels.

#### Configuration

```yaml
cost_control:
  budget:
    enabled: true
    daily_limit_usd: 100.0
    monthly_limit_usd: 3000.0
    per_request_limit_usd: 1.0
    reset_hour: 0  # Reset daily budget at midnight
```

#### Budget Tracking

- **Daily Budget**: Resets at configured hour (default: midnight)
- **Monthly Budget**: Resets on first day of month
- **Per-Request Budget**: Maximum cost per individual request

#### Budget Enforcement

- Requests exceeding per-request limit are rejected immediately
- Requests exceeding daily/monthly budget are rejected
- Budget is checked before processing requests

### 2. Token Usage Limits

Enforce limits on token usage per request.

#### Configuration

```yaml
cost_control:
  token_limits:
    enabled: true
    max_input_tokens: 100000   # ~75k words
    max_output_tokens: 4000
    max_total_tokens: 104000
```

#### Validation

- Input tokens validated before processing
- Output tokens estimated and validated
- Total tokens checked against limit

### 3. Cost-Based Routing

Automatically select cheaper models when appropriate.

#### Configuration

```yaml
cost_control:
  cost_routing:
    enabled: true
    prefer_cheaper_models: true
    cost_threshold_usd: 0.01
    quality_threshold: 0.7
```

#### How It Works

- Estimates cost before processing
- If cost > threshold and quality acceptable → Use cheaper model
- Maintains quality while reducing costs

## Usage

### Check Budget Status

```bash
curl http://localhost:8000/v1/cost/budget
```

Response:
```json
{
  "spending": {
    "daily": 45.23,
    "monthly": 1234.56
  },
  "limits": {
    "daily_limit_usd": 100.0,
    "monthly_limit_usd": 3000.0,
    "per_request_limit_usd": 1.0
  },
  "remaining": {
    "daily": 54.77,
    "monthly": 1765.44
  }
}
```

### Get Token Limits

```bash
curl http://localhost:8000/v1/cost/token-limits
```

### Get Cost Routing Config

```bash
curl http://localhost:8000/v1/cost/routing-config
```

## Cost Estimation

### How Costs Are Calculated

Costs are estimated based on:
- Provider pricing (per million tokens)
- Input token count
- Output token count

```python
cost = (input_tokens / 1_000_000) * input_price + 
       (output_tokens / 1_000_000) * output_price
```

### Token Counting

- Simple approximation: ~4 characters per token
- Actual counts from provider responses (when available)
- Includes system prompts and RAG context

## Budget Tracking

### In-Memory Tracking

- Daily spending tracked per day
- Monthly spending tracked per month
- Thread-safe with locks

### Production Considerations

For production, consider:
- Redis for distributed tracking
- Database for persistent storage
- Shared state across instances

## Monitoring

### Prometheus Metrics

- `cost_request_cost_usd` - Cost per request
- `cost_total_requests` - Total request count
- `cost_provider_api_calls_total` - API calls per provider
- `cost_provider_tokens_total` - Tokens per provider/model

### Logging

- Budget limit exceeded warnings
- Per-request limit exceeded errors
- Spending recorded in debug logs

## Best Practices

1. **Set Realistic Budgets**
   - Based on historical usage
   - Account for growth
   - Include buffer for spikes

2. **Monitor Spending**
   - Check budget status regularly
   - Set up alerts for high spending
   - Track trends over time

3. **Use Cost-Based Routing**
   - Enable for non-critical queries
   - Set appropriate quality thresholds
   - Monitor quality impact

4. **Configure Token Limits**
   - Prevent runaway requests
   - Match to use cases
   - Consider model limits

5. **Test Budget Scenarios**
   - Verify rejection at limits
   - Test daily/monthly resets
   - Validate per-request limits

## Hot Reload

Reload cost control policies:

```bash
curl -X POST http://localhost:8000/v1/cost/reload
```

## Configuration Examples

### Strict Budget Control

```yaml
cost_control:
  budget:
    daily_limit_usd: 50.0
    monthly_limit_usd: 1500.0
    per_request_limit_usd: 0.5
  token_limits:
    max_input_tokens: 50000
    max_output_tokens: 2000
  cost_routing:
    prefer_cheaper_models: true
    cost_threshold_usd: 0.005
```

### Flexible Budget

```yaml
cost_control:
  budget:
    daily_limit_usd: 500.0
    monthly_limit_usd: 15000.0
    per_request_limit_usd: 5.0
  token_limits:
    max_input_tokens: 200000
    max_output_tokens: 8000
  cost_routing:
    prefer_cheaper_models: false
```

## Related Documentation

- [Model Selection & Routing](./ROUTING_POLICIES.md)
- [Cost Optimization](./cost-optimization.md)
- [SLO/SLI Tracking](./slo-sli.md)

