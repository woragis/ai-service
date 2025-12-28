# Distributed Tracing Guide

This guide explains distributed tracing implementation in AI Service.

## Overview

Distributed tracing tracks requests across services using OpenTelemetry. Trace context is propagated via HTTP headers.

## Implementation

**Location:** `app/tracing.py`

**Features:**
- OpenTelemetry instrumentation
- Automatic FastAPI and HTTP client instrumentation
- OTLP exporter for Jaeger/Tempo
- Trace context propagation via HTTP headers
- Sampling (100% dev, 10% prod)

## How It Works

1. **Request Arrives**: FastAPI instrumentation creates span
2. **Trace Context**: Extracted from HTTP headers (`traceparent`, `tracestate`)
3. **Outgoing Requests**: Trace context added to HTTP headers
4. **Span Export**: Spans sent to OTLP collector/Jaeger
5. **Visualization**: View traces in Jaeger UI

## Configuration

**Environment Variables:**
```bash
OTLP_ENDPOINT=http://jaeger:4318  # OTLP endpoint
ENV=production                     # Environment (affects sampling)
```

**Sampling:**
- Development: 100% (all traces)
- Production: 10% (1 in 10 traces)

## Trace Context Propagation

Trace context is automatically propagated via HTTP headers:

**W3C Trace Context:**
- `traceparent`: Trace ID and span ID
- `tracestate`: Additional trace state

**Example:**
```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

## Integration with Other Services

When calling other services, trace context is automatically included:

```python
import httpx

async with httpx.AsyncClient() as client:
    # Trace context automatically added to headers
    response = await client.get("http://other-service/api")
```

## Viewing Traces

### Jaeger UI

1. Access Jaeger UI: `http://jaeger:16686`
2. Select service: `ai-service`
3. Search traces
4. View trace details

### Trace Information

Each trace contains:
- Service name
- Operation name
- Duration
- Tags (endpoint, status, etc.)
- Logs
- Child spans

## Best Practices

1. **Use Meaningful Names**: Service and operation names
2. **Add Context**: Add relevant tags to spans
3. **Sample Appropriately**: Balance detail vs. overhead
4. **Monitor Trace Volume**: Watch for high trace volume
5. **Correlate with Logs**: Use trace ID in logs

## Troubleshooting

### Traces Not Appearing

1. Check OTLP endpoint: `OTLP_ENDPOINT` environment variable
2. Verify Jaeger is running: `curl http://jaeger:16686`
3. Check sampling rate: May be too low
4. Review logs for errors

### High Trace Volume

1. Reduce sampling rate
2. Filter traces in Jaeger
3. Use trace sampling rules
4. Consider trace aggregation

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)

