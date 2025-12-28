# Performance Testing Guide

This guide explains how to run and interpret performance tests for the AI Service.

## Overview

Performance testing ensures the service can handle expected load and meets performance requirements. Tests include baseline, stress, and spike scenarios.

## Test Suite

Performance tests are located in `tests/performance/test_load.py` and include:

### Baseline Tests

**Normal load conditions** - Tests service under expected production load.

- `test_health_endpoint_baseline` - Health endpoint performance
- `test_agents_endpoint_baseline` - Agents list endpoint performance

**Expected Results:**
- Success rate: ≥ 99%
- P95 latency: < 100ms (health), < 200ms (agents)
- P99 latency: < 200ms (health), < 400ms (agents)

### Stress Tests

**High load conditions** - Tests service under maximum expected load.

- `test_concurrent_health_requests` - High concurrency test
- `test_sustained_load` - Sustained load over time

**Expected Results:**
- Success rate: ≥ 95%
- P95 latency: < 500ms
- Service should remain stable

### Spike Tests

**Sudden load increases** - Tests service response to traffic spikes.

- `test_sudden_load_spike` - Sudden 10x load increase

**Expected Results:**
- Success rate: ≥ 90%
- Service should handle spike gracefully
- Recovery time should be minimal

## Running Tests

### Local Execution

```bash
# Run all performance tests
pytest tests/performance/ -v -s

# Run specific test class
pytest tests/performance/test_load.py::TestBaselinePerformance -v -s

# Run with detailed output
pytest tests/performance/ -v -s --tb=short
```

### CI/CD Execution

Performance tests run automatically in CI/CD on every push/PR. Results are available in GitHub Actions artifacts.

## Interpreting Results

### Metrics Collected

Each test collects:
- **Total Requests**: Number of requests made
- **Success Rate**: Percentage of successful requests
- **Throughput**: Requests per second
- **Latency**: Min, max, mean, median, P50, P95, P99

### Example Output

```
Health Endpoint Baseline Performance:
  Total Requests: 100
  Success Rate: 100.00%
  Throughput: 500.00 req/s
  P95 Latency: 45.23ms
  P99 Latency: 78.45ms
```

### Performance Baselines

Establish performance baselines for your environment:

| Endpoint | P95 Target | P99 Target | Throughput Target |
|----------|------------|------------|-------------------|
| `/healthz` | < 50ms | < 100ms | > 1000 req/s |
| `/v1/agents` | < 100ms | < 200ms | > 500 req/s |
| `/v1/chat` | < 500ms | < 1000ms | > 100 req/s |

## Load Testing Tools

For more advanced load testing, consider:

### k6

```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 100 },
    { duration: '1m', target: 200 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  let response = http.get('http://ai-service:8080/healthz');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 100ms': (r) => r.timings.duration < 100,
  });
}
```

### Locust

```python
from locust import HttpUser, task, between

class AIServiceUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/healthz")
    
    @task(3)
    def chat(self):
        self.client.post("/v1/chat", json={
            "agent": "startup",
            "input": "Hello"
        })
```

## Performance Optimization

### Common Issues

1. **High Latency**
   - Check database queries
   - Review external API calls
   - Check resource limits
   - Review code for bottlenecks

2. **Low Throughput**
   - Check connection pooling
   - Review concurrent request handling
   - Check resource limits
   - Consider horizontal scaling

3. **High Error Rate**
   - Check external dependencies
   - Review error handling
   - Check resource exhaustion
   - Review rate limiting

### Optimization Strategies

1. **Caching**: Cache frequently accessed data
2. **Connection Pooling**: Reuse database/API connections
3. **Async Operations**: Use async/await for I/O operations
4. **Horizontal Scaling**: Add more replicas
5. **Resource Optimization**: Tune CPU/memory limits

## Continuous Performance Testing

### CI/CD Integration

Performance tests run in CI/CD on every push. Set up alerts for:
- Performance regressions
- Baseline violations
- Resource usage spikes

### Performance Budgets

Set performance budgets in CI/CD:
- P95 latency must not increase by > 10%
- Success rate must not decrease
- Throughput must not decrease by > 20%

## Best Practices

1. **Run Regularly**: Run performance tests before releases
2. **Establish Baselines**: Know your normal performance
3. **Monitor Trends**: Track performance over time
4. **Test Realistic Scenarios**: Test with production-like data
5. **Automate**: Include performance tests in CI/CD
6. **Document**: Document performance characteristics

## Troubleshooting

### Tests Failing

1. Check service is running: `curl http://localhost:8080/healthz`
2. Check resource limits: CPU/memory may be constrained
3. Check external dependencies: API keys, network connectivity
4. Review test configuration: Adjust thresholds if needed

### Inconsistent Results

1. Run tests multiple times: Average results
2. Check system load: Other processes may affect results
3. Use dedicated test environment: Avoid production interference
4. Warm up service: First requests may be slower

## References

- [k6 Documentation](https://k6.io/docs/)
- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/nonFunctionalRequirements.html)

