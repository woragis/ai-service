# CORS Configuration

## Overview

The AI service supports configurable Cross-Origin Resource Sharing (CORS) to allow web applications from different origins to access the API.

## Configuration

### Environment Variables

```bash
CORS_ENABLED=true
CORS_ALLOWED_ORIGINS=*
```

Or specify specific origins:

```bash
CORS_ENABLED=true
CORS_ALLOWED_ORIGINS=https://example.com,https://app.example.com
```

### Default Behavior

- **CORS_ENABLED**: `true` (enabled by default)
- **CORS_ALLOWED_ORIGINS**: `*` (all origins allowed by default)

## Implementation

CORS is implemented using FastAPI's `CORSMiddleware`:

```python
if settings.CORS_ENABLED:
    origins = settings.CORS_ALLOWED_ORIGINS.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

## Configuration Options

### Allow All Origins (Development)

```bash
CORS_ENABLED=true
CORS_ALLOWED_ORIGINS=*
```

### Specific Origins (Production)

```bash
CORS_ENABLED=true
CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

### Disable CORS

```bash
CORS_ENABLED=false
```

## Security Considerations

### Production

In production, always specify exact origins:

```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

Never use `*` in production for security reasons.

### Development

For local development, `*` is acceptable:

```bash
CORS_ALLOWED_ORIGINS=*
```

## CORS Headers

The middleware automatically handles:

- **Access-Control-Allow-Origin**: Set based on `CORS_ALLOWED_ORIGINS`
- **Access-Control-Allow-Methods**: All methods (`*`)
- **Access-Control-Allow-Headers**: All headers (`*`)
- **Access-Control-Allow-Credentials**: `true`

## Testing CORS

### Browser Test

```javascript
fetch('http://localhost:8000/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    agent: 'economist',
    input: 'Hello'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL Test

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Origin: https://example.com" \
  -H "Content-Type: application/json" \
  -d '{"agent": "economist", "input": "Hello"}' \
  -v
```

Check for `Access-Control-Allow-Origin` header in response.

## Kubernetes Configuration

### Ingress CORS

If using an ingress controller, you may also need to configure CORS there:

```yaml
annotations:
  nginx.ingress.kubernetes.io/enable-cors: "true"
  nginx.ingress.kubernetes.io/cors-allow-origin: "https://app.example.com"
  nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, OPTIONS"
  nginx.ingress.kubernetes.io/cors-allow-headers: "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range"
```

## Troubleshooting

### CORS Errors in Browser

1. Check `CORS_ENABLED` is `true`
2. Verify origin is in `CORS_ALLOWED_ORIGINS`
3. Check browser console for specific error
4. Verify preflight OPTIONS request succeeds

### Preflight Requests

The middleware automatically handles OPTIONS preflight requests.

## Related Documentation

- [Kubernetes Deployment](./KUBERNETES_DEPLOYMENT.md)
- [Configuration](./README.md)

