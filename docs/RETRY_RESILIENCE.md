# Retry & Resilience Policies

## Overview

The AI service implements comprehensive retry and resilience mechanisms to handle transient failures, timeouts, and provider outages gracefully.

## Features

### 1. Retry Strategies

Automatic retry with configurable backoff strategies for transient failures.

#### Configuration

```yaml
resilience:
  retry:
    enabled: true
    max_attempts: 3
    initial_delay_seconds: 0.5
    backoff_factor: 2.0
    max_delay_seconds: 10.0
    retry_on_status_codes: [429, 500, 502, 503, 504]
    retry_on_exceptions:
      - "httpx.ConnectError"
      - "httpx.TimeoutException"
      - "openai.APITimeoutError"
```

#### Backoff Types

- **Exponential Backoff**: Delay doubles after each attempt (default)
- **Linear Backoff**: Fixed delay increment
- **Fixed Backoff**: Constant delay between attempts

#### Per-Provider Retry

```yaml
resilience:
  retry_strategies:
    openai:
      max_attempts: 3
      initial_delay_seconds: 0.5
      backoff_factor: 2.0
    anthropic:
      max_attempts: 5
      initial_delay_seconds: 1.0
      backoff_factor: 1.5
```

### 2. Circuit Breakers

See [Circuit Breakers Documentation](./CIRCUIT_BREAKERS.md) for detailed information.

### 3. Timeout Policies

Configurable timeouts per provider, model, and endpoint.

#### Configuration

```yaml
resilience:
  timeout:
    enabled: true
    default_timeout_seconds: 90
    per_provider_timeouts:
      openai: 120
      anthropic: 120
      cipher: 60
    per_model_timeouts:
      gpt-4o-mini: 60
      claude-3-haiku-20240307: 60
```

#### How It Works

- Default timeout applies to all requests
- Provider-specific timeouts override default
- Model-specific timeouts override provider timeouts
- Endpoint-specific timeouts can be specified in code

### 4. Graceful Degradation

Automatic model downgrade or provider switching when failures occur.

#### Configuration

```yaml
resilience:
  degradation:
    enabled: true
    degrade_to_provider: "xai"
    degrade_to_model: "grok-1"
    message: "Service is currently degraded. Please try again later."
```

#### Degradation Conditions

- High error rate (> threshold)
- High latency (> threshold)
- Circuit breaker open
- Rate limit exceeded

## Usage

### Automatic Application

Resilience features are automatically applied when using:

```python
from app.routing import execute_with_fallback

result = await execute_with_fallback(
    provider="openai",
    model="gpt-4o",
    fallback_chain=["anthropic", "xai"],
    execute_fn=your_function,
    endpoint="/v1/chat"
)
```

This function automatically:
1. Checks circuit breaker state
2. Applies timeout
3. Retries on transient failures
4. Falls back to next provider on failure
5. Applies graceful degradation if needed

### Manual Retry

```python
from app.resilience import retry_with_backoff

result = await retry_with_backoff(
    your_async_function,
    retry_policy_name="default"
)
```

### Manual Timeout

```python
from app.resilience import apply_timeout

result = await apply_timeout(
    your_async_function,
    provider="openai",
    model="gpt-4o"
)
```

### Circuit Breaker

```python
from app.resilience.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker("openai")
result = await breaker.execute(your_async_function)
```

## Monitoring

### Metrics

Resilience events are logged with structured logging:

- `Circuit breaker tripped to OPEN` - Provider failing
- `Function failed, retrying...` - Retry attempt
- `Execution successful` - Success after retry
- `Applying graceful degradation` - Degradation triggered

### Prometheus Metrics

Circuit breaker state and retry counts can be tracked via custom metrics (if implemented).

## Best Practices

1. **Configure Appropriate Retry Counts**
   - Too few: May fail on transient issues
   - Too many: Wastes time and resources

2. **Set Realistic Timeouts**
   - Consider provider SLAs
   - Account for network latency
   - Model-specific timeouts for slower models

3. **Use Fallback Chains**
   - Always configure multiple providers
   - Order by preference/quality
   - Include cheaper fallback options

4. **Monitor Circuit Breakers**
   - Track how often circuits open
   - Adjust thresholds based on real behavior
   - Alert on frequent circuit trips

5. **Test Degradation Scenarios**
   - Verify fallback providers work
   - Ensure degraded responses are acceptable
   - Test recovery from degraded state

## Hot Reload

Reload resilience policies without restarting:

```bash
curl -X POST http://localhost:8000/v1/resilience/reload
```

## Configuration Examples

### High Availability Setup

```yaml
resilience:
  retry:
    max_attempts: 5
    initial_delay_seconds: 0.5
    backoff_factor: 2.0
  circuit_breaker:
    failure_threshold: 3
    recovery_timeout_seconds: 30
  timeout:
    default_timeout_seconds: 60
```

### Cost-Optimized Setup

```yaml
resilience:
  retry:
    max_attempts: 2  # Fewer retries to save costs
  circuit_breaker:
    failure_threshold: 5
    recovery_timeout_seconds: 60  # Longer recovery
  degradation:
    enabled: true
    degrade_to_provider: "xai"  # Cheaper fallback
```

## Related Documentation

- [Circuit Breakers](./CIRCUIT_BREAKERS.md)
- [Model Selection & Routing](./ROUTING_POLICIES.md)
- [Request Timeouts](./request-timeouts.md)
- [Graceful Shutdown](./graceful-shutdown.md)

