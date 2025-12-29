# Health Checks

## Overview

The AI service implements health check endpoints for monitoring service availability and external dependencies.

## Endpoints

### Basic Health Check

```
GET /healthz
```

Returns simple health status:

```json
{
  "status": "healthy",
  "checks": [
    {
      "name": "service",
      "status": "ok"
    }
  ]
}
```

### Status Values

- **healthy**: All checks passed
- **unhealthy**: One or more checks failed

### Check Status

- **ok**: Check passed
- **error**: Check failed

## Health Check System

The health check system is implemented in `app/health.py`:

```python
def check_health() -> Dict[str, Any]:
    """
    Perform health checks for the AI service.
    
    Returns:
        Dictionary with status and checks
    """
    checks = []
    
    # Check service availability (always ok if endpoint is reachable)
    checks.append({
        "name": "service",
        "status": "ok"
    })
    
    # Determine overall status
    has_errors = any(check["status"] == "error" for check in checks)
    status = "unhealthy" if has_errors else "healthy"
    
    return {
        "status": status,
        "checks": checks
    }
```

## Caching

Health checks are cached for 5 seconds to reduce load:

```python
_cache_ttl = 5.0  # Cache for 5 seconds
```

## Usage

### Kubernetes Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Kubernetes Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Docker Healthcheck

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1
```

### Monitoring

```bash
# Check health
curl http://localhost:8000/healthz

# Monitor with watch
watch -n 5 curl -s http://localhost:8000/healthz | jq
```

## Extending Health Checks

### Add Dependency Checks

Modify `app/health.py` to add checks:

```python
def check_health() -> Dict[str, Any]:
    checks = []
    
    # Service check
    checks.append({"name": "service", "status": "ok"})
    
    # Vector DB check
    try:
        from app.knowledge_base.vector_db import get_vector_db
        vector_db = get_vector_db()
        # Perform actual check
        checks.append({"name": "vector_db", "status": "ok"})
    except Exception as e:
        checks.append({"name": "vector_db", "status": "error", "error": str(e)})
    
    # File storage check
    try:
        from app.knowledge_base.file_storage import get_file_storage
        file_storage = get_file_storage()
        # Perform actual check
        checks.append({"name": "file_storage", "status": "ok"})
    except Exception as e:
        checks.append({"name": "file_storage", "status": "error", "error": str(e)})
    
    # Determine overall status
    has_errors = any(check["status"] == "error" for check in checks)
    status = "unhealthy" if has_errors else "healthy"
    
    return {"status": status, "checks": checks}
```

### Provider Health Checks

Check external provider availability:

```python
# OpenAI check
try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # Quick test call or connection check
    checks.append({"name": "openai", "status": "ok"})
except Exception as e:
    checks.append({"name": "openai", "status": "error", "error": str(e)})
```

## Best Practices

1. **Keep Checks Fast** - Health checks should complete quickly (< 1 second)
2. **Cache Results** - Use caching to reduce load
3. **Check Critical Dependencies** - Only check essential services
4. **Provide Error Details** - Include error messages for debugging
5. **Separate Liveness/Readiness** - Use different endpoints if needed

## Advanced Health Checks

### Separate Liveness and Readiness

Create separate endpoints:

```python
@app.get("/healthz/live")
async def liveness():
    """Liveness probe - is the service running?"""
    return {"status": "alive"}

@app.get("/healthz/ready")
async def readiness():
    """Readiness probe - is the service ready to accept traffic?"""
    checks = []
    # Check dependencies
    # ...
    return {"status": "ready", "checks": checks}
```

### Detailed Health Information

Include more information:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "checks": [
    {
      "name": "service",
      "status": "ok",
      "response_time_ms": 5
    }
  ]
}
```

## Monitoring Integration

### Prometheus

Health check status can be exposed as a metric:

```python
from prometheus_client import Gauge

health_status = Gauge('service_health', 'Service health status', ['check'])

# In health check
health_status.labels(check='service').set(1 if status == "ok" else 0)
```

### Alerting

Set up alerts based on health check failures:

```yaml
# Prometheus alert
- alert: ServiceUnhealthy
  expr: service_health{check="service"} == 0
  for: 1m
  annotations:
    summary: "Service is unhealthy"
```

## Related Documentation

- [Kubernetes Deployment](./KUBERNETES_DEPLOYMENT.md)
- [Monitoring & Alerting](./alerting.md)
- [SLO/SLI Tracking](./slo-sli.md)

