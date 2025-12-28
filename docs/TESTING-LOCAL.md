# Testing AI Service Locally in Docker

This guide explains how to test the AI Service locally in a Docker container.

## Quick Start

### Using PowerShell (Windows)

```powershell
.\test-local.ps1
```

### Using Bash (Linux/Mac)

```bash
./test-local.sh
```

### Using Docker Compose

```bash
docker-compose -f docker-compose.test.yml up --build
```

## Manual Testing

### 1. Build Docker Image

```bash
docker build -t ai-service:local .
```

### 2. Create .env File

Copy `env.sample` to `.env` and add your API keys:

```bash
cp env.sample .env
# Edit .env with your API keys
```

Required API keys (at least one):
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `CIPHER_API_KEY` (already in env.sample)

### 3. Run Container

```bash
docker run -d \
  --name ai-service-test \
  -p 8000:8000 \
  --env-file .env \
  -e ENV=development \
  -e LOG_LEVEL=info \
  ai-service:local
```

### 4. Test Endpoints

**Health Check:**
```bash
curl http://localhost:8000/healthz
```

**List Agents:**
```bash
curl http://localhost:8000/v1/agents
```

**Chat (OpenAI):**
```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "startup",
    "input": "What is a startup?",
    "provider": "openai"
  }'
```

**Chat (Anthropic):**
```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "startup",
    "input": "What is a startup?",
    "provider": "anthropic"
  }'
```

**Metrics:**
```bash
curl http://localhost:8000/metrics
```

### 5. View Logs

```bash
docker logs -f ai-service-test
```

### 6. Stop Container

```bash
docker rm -f ai-service-test
```

## Features Tested in Docker

When running in Docker, these features are active:

✅ **Request Timeouts** - Automatically enforced
✅ **Graceful Shutdown** - Handles SIGTERM/SIGINT
✅ **Distributed Tracing** - OpenTelemetry (if OTLP endpoint configured)
✅ **SLO/SLI Tracking** - Metrics at `/metrics`
✅ **Cost Tracking** - Metrics at `/metrics`

## Troubleshooting

### Service Won't Start

1. Check logs: `docker logs ai-service-test`
2. Verify API keys in `.env`
3. Check port 8000 is available: `netstat -an | grep 8000`

### Health Check Fails

1. Wait a few seconds for service to start
2. Check logs for errors
3. Verify environment variables are set

### API Calls Fail

1. Verify API keys are correct in `.env`
2. Check provider availability
3. Review logs for specific errors

## Environment Variables

Key environment variables:

- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `CIPHER_API_KEY` - Cipher API key (default in env.sample)
- `ENV` - Environment (development/production)
- `LOG_LEVEL` - Log level (info/debug)
- `CORS_ENABLED` - Enable CORS (true/false)
- `OTLP_ENDPOINT` - OpenTelemetry endpoint (optional)

## Next Steps

After testing locally:
1. Verify all endpoints work
2. Check metrics at `/metrics`
3. Test graceful shutdown: `docker stop ai-service-test`
4. Review logs for any issues

