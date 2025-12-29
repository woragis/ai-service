# Circuit Breakers

## Overview

The AI service implements a circuit breaker pattern to prevent cascading failures when external LLM providers are experiencing issues. Circuit breakers automatically stop requests to failing providers and allow them to recover gracefully.

## How It Works

### States

The circuit breaker has three states:

1. **CLOSED** (Normal Operation)
   - Requests flow through normally
   - Failures are tracked
   - If failure threshold is reached, transitions to OPEN

2. **OPEN** (Failing)
   - All requests are immediately rejected
   - No calls are made to the provider
   - After recovery timeout, transitions to HALF_OPEN

3. **HALF_OPEN** (Testing Recovery)
   - Allows a limited number of test requests
   - If successful, transitions to CLOSED
   - If still failing, transitions back to OPEN

### Configuration

Circuit breakers are configured via the resilience policy (`resilience/policies/resilience.yaml`):

```yaml
resilience:
  circuit_breaker:
    enabled: true
    failure_threshold: 5        # Number of consecutive failures to open
    success_threshold: 2          # Number of successes to close from half-open
    timeout: 60                  # Seconds before attempting half-open
    half_open_max_calls: 3       # Max test requests in half-open state
```

### Per-Provider Configuration

You can configure circuit breakers per provider:

```yaml
resilience:
  circuit_breakers:
    openai:
      failure_threshold: 5
      success_threshold: 2
      timeout: 60
      half_open_max_calls: 3
    anthropic:
      failure_threshold: 3
      success_threshold: 1
      timeout: 30
      half_open_max_calls: 2
```

## Usage

Circuit breakers are automatically applied when using the `execute_with_fallback` function in the routing system. They check the circuit state before attempting a provider call and record success/failure after execution.

### Example Flow

1. **Normal Operation (CLOSED)**
   ```
   Request → Circuit Breaker → Provider API → Success → Record Success
   ```

2. **Failure Detected**
   ```
   Request → Circuit Breaker → Provider API → Failure → Record Failure
   After 5 failures → Circuit Opens
   ```

3. **Circuit Open**
   ```
   Request → Circuit Breaker (OPEN) → Immediate Rejection → Use Fallback Provider
   ```

4. **Recovery Attempt (HALF_OPEN)**
   ```
   After 60s timeout → Circuit HALF_OPEN
   Test Request → Provider API → Success → Record Success
   After 2 successes → Circuit CLOSED
   ```

## Benefits

- **Prevents Cascading Failures**: Stops sending requests to failing providers
- **Fast Failure**: Immediate rejection when circuit is open (no waiting for timeouts)
- **Automatic Recovery**: Tests provider health periodically
- **Resource Protection**: Reduces load on failing services

## Monitoring

Circuit breaker state changes are logged:
- `Circuit breaker tripped to OPEN` - Provider is failing
- `Circuit breaker moved to HALF-OPEN` - Testing recovery
- `Circuit breaker reset to CLOSED` - Provider recovered

## Best Practices

1. **Set Appropriate Thresholds**
   - Lower thresholds for critical providers
   - Higher thresholds for less critical providers

2. **Configure Timeouts**
   - Shorter timeouts for fast recovery testing
   - Longer timeouts for stable providers

3. **Use Fallback Chains**
   - Always configure fallback providers
   - Circuit breakers work best with multiple provider options

4. **Monitor Circuit States**
   - Track how often circuits open/close
   - Adjust thresholds based on real-world behavior

## Hot Reload

Circuit breaker configurations can be reloaded without restarting the service:

```bash
curl -X POST http://localhost:8000/v1/resilience/reload
```

## Related Documentation

- [Retry & Resilience Policies](./RETRY_RESILIENCE.md)
- [Model Selection & Routing](./ROUTING_POLICIES.md)
- [Advanced Deployment](./advanced-deployment.md)

