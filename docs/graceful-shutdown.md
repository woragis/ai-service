# Graceful Shutdown Guide

This guide explains graceful shutdown implementation in AI Service.

## Overview

Graceful shutdown ensures the service shuts down cleanly:
- In-flight requests complete
- Connections close properly
- Resources are cleaned up
- No request loss

## How It Works

1. **Signal Received**: SIGTERM or SIGINT
2. **Shutdown Event**: Sets global shutdown event
3. **Stop Accepting**: FastAPI stops accepting new requests
4. **Wait for Completion**: Allows in-flight requests to complete (2 seconds)
5. **Cleanup**: Closes connections, cleans up resources
6. **Exit**: Process exits

## Implementation

**Location:** `app/graceful_shutdown.py`

Integrated via FastAPI lifespan:
```python
app = FastAPI(lifespan=lifespan)
```

## Signals Handled

- **SIGTERM**: Termination signal (Kubernetes)
- **SIGINT**: Interrupt signal (Ctrl+C)
- **SIGBREAK**: Windows break signal

## Configuration

Grace period for in-flight requests: 2 seconds

To change, edit `app/graceful_shutdown.py`:
```python
await asyncio.sleep(2)  # Change this value
```

## Kubernetes Integration

Kubernetes sends SIGTERM before killing the pod:

1. **Termination Grace Period**: Set in deployment (default: 30s)
2. **PreStop Hook**: Optional, for additional cleanup
3. **Readiness Probe**: Removes pod from service endpoints

Example:
```yaml
spec:
  terminationGracePeriodSeconds: 30
  containers:
  - name: ai-service
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 5"]
```

## Testing

Test graceful shutdown:

```bash
# Start service
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, send SIGTERM
kill -TERM <pid>

# Or use Ctrl+C (SIGINT)
```

## Monitoring

Monitor shutdown events:
- Check logs for "shutting down" messages
- Monitor request completion during shutdown
- Verify no request loss

## Best Practices

1. **Set Appropriate Grace Period**: Balance between cleanup and speed
2. **Monitor Shutdown Time**: Ensure it completes within termination grace period
3. **Test Regularly**: Test shutdown in staging
4. **Handle Long Requests**: Consider request timeouts

## Troubleshooting

### Shutdown Takes Too Long

1. Check for long-running requests
2. Review grace period
3. Check resource cleanup code
4. Consider reducing grace period

### Requests Lost During Shutdown

1. Increase termination grace period
2. Increase grace period in code
3. Check for blocking operations
4. Review request timeout settings

