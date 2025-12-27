# AI Service v1.0.0

## Overview

The AI Service is a production-ready FastAPI-based service that provides a unified interface for interacting with multiple Large Language Model (LLM) providers through specialized AI agents. This initial stable release features multi-provider support, streaming responses, image generation, comprehensive observability, and a flexible agent architecture.

## Key Features

### Core Functionality
- **Multi-Provider LLM Support**: Unified interface for OpenAI, Anthropic (Claude), xAI (Grok), Manus, and Cipher (NoFilterGPT)
- **AI Agent System**: Specialized agents with distinct personas for different use cases
  - **Economist**: Macro and microeconomics analysis, market insights, unit economics
  - **Strategist**: Business strategy, positioning, go-to-market planning, competitive analysis
  - **Entrepreneur**: Pragmatic startup advice, MVP scoping, scrappy tactics, validation
  - **Startup Advisor**: Product thinking, growth, fundraising, execution advice
  - **Auto Selection**: Intelligent agent selection based on input keywords
- **Streaming Chat**: Server-sent events (SSE) for real-time token streaming
- **Image Generation**: Generate images via Cipher provider (NoFilterGPT)

### Production Features
- **FastAPI Framework**: Modern async Python web framework with automatic API documentation
- **Health Check Endpoint**: HTTP endpoint at `/healthz` for Kubernetes liveness/readiness probes
- **Prometheus Metrics**: Comprehensive metrics exposed at `/metrics` endpoint via prometheus-fastapi-instrumentator
- **Structured Logging**: JSON logging in production, text logging in development with structlog
- **OpenTelemetry Tracing**: Distributed tracing support with OTLP exporter (Jaeger compatible)
- **Request ID Middleware**: Automatic trace ID generation and propagation via `X-Trace-ID` headers
- **HTTP Request Logging**: Automatic structured logging of all HTTP requests with duration, status, and context

### Configuration & Flexibility
- **Environment-based Configuration**: All settings via environment variables
- **CORS Support**: Configurable CORS for cross-origin requests
- **Provider Factory Pattern**: Easy to add new LLM providers
- **Model Overrides**: Per-request model and temperature overrides
- **System Message Injection**: Optional custom system instructions per request

### Code Quality
- **Comprehensive Testing**: Unit tests and integration tests included
- **Test Coverage**: Coverage reporting with pytest-cov
- **Type Hints**: Full type annotation support
- **Clean Architecture**: Separation of concerns with providers, agents, and middleware
- **Async/Await**: Full async support for high concurrency

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP/WebSocket
       │
┌──────▼──────────────────┐
│   FastAPI Application   │
│                         │
│  ┌──────────────────┐   │
│  │  Middleware      │   │
│  │  - Request ID    │   │
│  │  - Logging       │   │
│  │  - Tracing       │   │
│  └────────┬─────────┘   │
│           │            │
│  ┌────────▼─────────┐   │
│  │  Agent Registry  │   │
│  │  - Economist     │   │
│  │  - Strategist    │   │
│  │  - Entrepreneur  │   │
│  │  - Startup       │   │
│  └────────┬─────────┘   │
│           │            │
│  ┌────────▼─────────┐   │
│  │ Provider Factory │   │
│  └────────┬─────────┘   │
└───────────┼─────────────┘
            │
    ┌───────┴────────┐
    │                │
┌───▼────┐      ┌───▼─────┐
│ OpenAI │      │Anthropic│
└────────┘      └─────────┘
    │                │
┌───▼────┐      ┌───▼─────┐
│  xAI   │      │  Manus  │
└────────┘      └─────────┘
    │                │
┌───▼────┐      ┌───▼─────┐
│ Cipher │      │ ...     │
└────────┘      └─────────┘
```

## Dependencies

### Core Framework
- **fastapi**: Modern async web framework
- **uvicorn**: ASGI server with standard extras
- **pydantic**: Data validation and settings management

### LLM Integration
- **langchain**: LLM framework and abstractions
- **langchain-openai**: OpenAI integration
- **langchain-anthropic**: Anthropic Claude integration
- **openai**: OpenAI Python SDK
- **anthropic**: Anthropic Python SDK
- **httpx**: Async HTTP client for custom providers

### Observability
- **structlog**: Structured logging
- **prometheus-client**: Prometheus metrics
- **prometheus-fastapi-instrumentator**: FastAPI metrics auto-instrumentation
- **opentelemetry-api/sdk**: OpenTelemetry tracing
- **opentelemetry-exporter-otlp-proto-http**: OTLP HTTP exporter
- **opentelemetry-instrumentation-fastapi**: FastAPI auto-instrumentation

### Development & Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking support
- **python-dotenv**: Environment variable management
- **tenacity**: Retry logic (in dependencies)

## API Endpoints

### Chat Endpoints

#### POST `/v1/chat`
Synchronous chat completion endpoint.

**Request:**
```json
{
  "agent": "economist",
  "input": "Analyze the current market conditions",
  "system": "Focus on actionable insights",
  "temperature": 0.7,
  "model": "gpt-4o",
  "provider": "openai"
}
```

**Response:**
```json
{
  "agent": "economist",
  "output": "Based on current market indicators..."
}
```

#### POST `/v1/chat/stream`
Streaming chat completion endpoint (Server-Sent Events).

**Request:** Same as `/v1/chat`

**Response:** NDJSON stream:
```
{"delta": "Based"}
{"delta": " on"}
{"delta": " current"}
...
{"done": true, "output": "Complete response"}
```

### Image Generation

#### POST `/v1/images`
Generate images using Cipher provider.

**Request:**
```json
{
  "provider": "cipher",
  "prompt": "A futuristic cityscape at sunset",
  "n": 1,
  "size": "1024x1024"
}
```

**Response:**
```json
{
  "data": [
    {
      "url": "https://...",
      "b64_json": null
    }
  ]
}
```

### Utility Endpoints

#### GET `/v1/agents`
List available agent names.

**Response:**
```json
["economist", "strategist", "entrepreneur", "startup"]
```

#### GET `/healthz`
Health check endpoint for Kubernetes probes.

**Response:**
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

#### GET `/metrics`
Prometheus metrics endpoint (auto-instrumented).

## Configuration Variables

### Core Configuration
- `ENV`: Environment mode - "development" or "production" (affects logging)
- `CORS_ENABLED`: Enable CORS (default: true)
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed origins (default: "*")
- `DEFAULT_TEMPERATURE`: Default temperature for LLM calls (default: 0.3)

### OpenAI Configuration
- `OPENAI_API_KEY`: OpenAI API key (required for "openai" provider)
- `OPENAI_MODEL`: Default OpenAI model (default: "gpt-4o-mini")

### Anthropic Configuration
- `ANTHROPIC_API_KEY`: Anthropic API key (required for "anthropic" provider)
- `ANTHROPIC_MODEL`: Default Anthropic model (default: "claude-3-5-sonnet-latest")

### xAI Configuration
- `XAI_API_KEY`: xAI API key (required for "xai" provider)
- `XAI_BASE_URL`: xAI base URL (default: "https://api.x.ai/v1")
- `XAI_MODEL`: Default xAI model (default: "grok-beta")

### Manus Configuration
- `MANUS_API_KEY`: Manus API key (required for "manus" provider)
- `MANUS_BASE_URL`: Manus base URL (required)
- `MANUS_MODEL`: Default Manus model (default: "manus-chat")

### Cipher Configuration
- `CIPHER_API_KEY`: Cipher API key (required for "cipher" provider)
- `CIPHER_BASE_URL`: Cipher chat completions URL (default: "https://api.nofiltergpt.com/v1/chat/completions")
- `CIPHER_MAX_TOKENS`: Max tokens for Cipher (default: 800)
- `CIPHER_TOP_P`: Top-p sampling for Cipher (default: 1.0)
- `CIPHER_IMAGE_URL`: Cipher image generation URL (default: "https://api.nofiltergpt.com/v1/images/generations")
- `CIPHER_IMAGE_SIZE`: Default image size (default: "1024x1024")
- `CIPHER_IMAGE_N`: Default number of images (default: 1)

### Observability Configuration
- `OTLP_ENDPOINT`: OpenTelemetry OTLP endpoint (default: "http://jaeger:4318")
- `LOG_TO_FILE`: Enable file logging in development (default: false)
- `LOG_DIR`: Directory for log files (default: "logs")

## Agent Personas

### Economist Agent
Focused on economic analysis, market conditions, policy impacts, unit economics, and risk assessment. Ideal for:
- Market analysis
- Pricing strategies
- Economic policy impact
- Financial modeling insights

### Strategist Agent
Expert in business strategy, positioning, competitive analysis, and go-to-market planning. Ideal for:
- Competitive positioning
- Market entry strategies
- Business model design
- Strategic prioritization

### Entrepreneur Agent
Pragmatic startup founder perspective with bias to action and validation. Ideal for:
- MVP scoping
- Rapid validation
- Scrappy tactics
- Launch planning

### Startup Advisor Agent
Comprehensive startup mentorship covering product, growth, fundraising, and execution. Ideal for:
- Product strategy
- Growth tactics
- Fundraising advice
- Execution frameworks

### Auto Selection
Automatically selects the most appropriate agent based on input keywords:
- Economics/market terms → Economist
- Strategy/positioning terms → Strategist
- MVP/validation terms → Entrepreneur
- Default → Startup Advisor

## Observability

### Structured Logging
- **Production**: JSON format for log aggregation systems
- **Development**: Human-readable text format
- **Fields**: Automatic service name, trace ID, request context
- **Levels**: DEBUG (dev), INFO (prod) with automatic error logging

### Distributed Tracing
- **OpenTelemetry**: Full OTLP support with Jaeger compatibility
- **Auto-instrumentation**: FastAPI and HTTP requests automatically traced
- **Sampling**: 100% in development, 10% in production
- **Context Propagation**: Trace IDs via `X-Trace-ID` headers

### Metrics
- **HTTP Metrics**: Request count, duration, status codes
- **Endpoint Metrics**: Per-endpoint performance tracking
- **Custom Metrics**: Extensible metric system via Prometheus client

## Development

### Testing
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests
make test-integration

# Run with coverage
make test-cov

# Clean test artifacts
make clean
```

### Running Locally
```bash
# Install dependencies
make install

# Run with uvicorn (development)
uvicorn app.main:app --reload --port 8000

# Run with environment file
ENV=development uvicorn app.main:app --reload
```

### Docker
```bash
# Build image
docker build -t ai-service .

# Run container
docker run -p 8000:8000 --env-file .env ai-service
```

## Deployment

### Kubernetes
- **Port**: 8000 (default)
- **Health Check**: `GET /healthz`
- **Liveness Probe**: Every 10s, timeout 5s
- **Readiness Probe**: Every 10s, timeout 5s
- **Resource Requirements**: Adjust based on concurrent request load

### Scaling
- **Horizontal Scaling**: Stateless design allows multiple instances
- **Load Balancing**: Use Kubernetes service or ingress load balancer
- **Connection Pooling**: httpx async client handles concurrent connections efficiently

### Environment Variables
Use Kubernetes Secrets or ConfigMaps for sensitive configuration:
- API keys → Secrets
- Service configuration → ConfigMaps

## Documentation

- **HEALTH_CHECK.md**: Detailed health check documentation
- **LOGGING.md**: Structured logging guidelines and usage
- **ENVIRONMENT.md**: Environment variable reference
- **tests/README.md**: Testing documentation

## Breaking Changes

None - This is the initial release.

## Future Enhancements

Potential improvements for future versions:
- Additional LLM providers (Google Gemini, Mistral, etc.)
- Custom agent creation API
- Conversation memory/context management
- Rate limiting and usage quotas
- Multi-modal support (audio, video)
- Agent chaining and workflows
- Caching layer for repeated queries
- Cost tracking and analytics
- A/B testing for agent responses

## Contributors

Initial release by the Woragis team.

## License

Part of the Woragis backend infrastructure.

