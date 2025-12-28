# Request Timeouts Guide

This guide explains request timeout implementation in AI Service.

## Overview

Request timeouts prevent long-running requests from consuming resources indefinitely. Each endpoint has a configurable timeout based on expected processing time.

## Configuration

Timeouts are configured in `app/middleware_timeout.py`:

```python
ENDPOINT_TIMEOUTS = {
    "/v1/chat": 60,           # 1 minute
    "/v1/chat/stream": 300,   # 5 minutes
    "/v1/images": 120,        # 2 minutes
    "/v1/agents": 5,          # 5 seconds
    "/healthz": 5,           # 5 seconds
}
```

Default timeout: 300 seconds (5 minutes)

## How It Works

1. Request comes in
2. Middleware checks endpoint timeout
3. Request is wrapped with `asyncio.wait_for()`
4. If timeout exceeded, returns 504 Gateway Timeout
5. Request is cancelled

## Customizing Timeouts

Edit `app/middleware_timeout.py`:

```python
ENDPOINT_TIMEOUTS = {
    "/v1/chat": 120,  # Increase to 2 minutes
}
```

## Monitoring

Timeout events are logged:
```
WARN: request timeout path=/v1/chat timeout=60 method=POST
```

Monitor timeout rate:
```promql
rate(http_requests_total{status="504"}[5m])
```

## Best Practices

1. **Set Realistic Timeouts**: Based on actual processing time
2. **Monitor Timeout Rate**: Alert if timeout rate is high
3. **Adjust as Needed**: Update timeouts based on metrics
4. **Consider Provider Limits**: Account for external API timeouts

## Troubleshooting

### Too Many Timeouts

1. Check external API response times
2. Review timeout values (may be too low)
3. Check for performance issues
4. Consider increasing timeout

### Requests Not Timing Out

1. Verify middleware is enabled
2. Check timeout configuration
3. Verify asyncio is working correctly

