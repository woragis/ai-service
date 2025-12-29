# Request Overrides

## Overview

The AI service supports per-request overrides for model selection, temperature, and other parameters. This allows fine-grained control over individual requests without changing global configuration.

## Supported Overrides

### 1. Model Override

Specify a different model for a specific request:

```json
{
  "agent": "economist",
  "input": "Explain inflation",
  "model": "gpt-4o"
}
```

### 2. Temperature Override

Adjust temperature (creativity) for a specific request:

```json
{
  "agent": "economist",
  "input": "Explain inflation",
  "temperature": 0.7
}
```

### 3. Provider Override

Select a specific provider:

```json
{
  "agent": "economist",
  "input": "Explain inflation",
  "provider": "anthropic"
}
```

### 4. System Prompt Override

Add additional system instructions:

```json
{
  "agent": "economist",
  "input": "Explain inflation",
  "system": "Focus on practical implications for businesses"
}
```

## Usage Examples

### High Creativity Request

```json
{
  "agent": "entrepreneur",
  "input": "Generate creative startup ideas",
  "temperature": 0.9,
  "model": "gpt-4o"
}
```

### Precise Technical Request

```json
{
  "agent": "developer",
  "input": "Explain this code",
  "temperature": 0.1,
  "model": "gpt-4o"
}
```

### Cost-Optimized Request

```json
{
  "agent": "economist",
  "input": "Simple question",
  "model": "gpt-4o-mini",
  "temperature": 0.3
}
```

## Temperature Guidelines

- **0.0-0.3**: Very focused, deterministic (good for factual queries)
- **0.3-0.7**: Balanced (default: 0.3)
- **0.7-1.0**: Creative, varied responses
- **1.0-2.0**: Highly creative, unpredictable

## Model Selection

### OpenAI Models

- `gpt-4o`: Best quality, higher cost
- `gpt-4o-mini`: Good quality, lower cost
- `gpt-4-turbo`: Previous generation
- `gpt-3.5-turbo`: Legacy, cheapest

### Anthropic Models

- `claude-3-opus-20240229`: Highest quality
- `claude-3-5-sonnet-latest`: Balanced quality/speed
- `claude-3-haiku-20240307`: Fast, cost-effective

### xAI Models

- `grok-beta`: Cost-effective option

## Override Priority

1. **Request-level overrides** (highest priority)
2. **Agent policy defaults**
3. **Global configuration** (lowest priority)

## Best Practices

1. **Use Appropriate Temperature** - Match to use case
2. **Select Right Model** - Balance quality and cost
3. **Override Sparingly** - Use defaults when possible
4. **Monitor Costs** - Overrides can increase costs
5. **Test Overrides** - Verify behavior before production

## Cost Implications

### Model Costs

- **GPT-4o**: ~$5/$15 per million tokens
- **GPT-4o-mini**: ~$0.15/$0.60 per million tokens
- **Claude 3.5 Sonnet**: ~$3/$15 per million tokens
- **Claude Haiku**: ~$0.25/$1.25 per million tokens

### Temperature Impact

Temperature doesn't directly affect cost, but:
- Higher temperature may generate longer responses
- Longer responses = more output tokens = higher cost

## API Examples

### Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/v1/chat",
    json={
        "agent": "economist",
        "input": "Explain inflation",
        "model": "gpt-4o",
        "temperature": 0.5,
        "system": "Use simple language"
    }
)
```

### JavaScript

```javascript
fetch('http://localhost:8000/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    agent: 'economist',
    input: 'Explain inflation',
    model: 'gpt-4o',
    temperature: 0.5,
    system: 'Use simple language'
  })
})
```

### cURL

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "economist",
    "input": "Explain inflation",
    "model": "gpt-4o",
    "temperature": 0.5,
    "system": "Use simple language"
  }'
```

## Streaming Overrides

All overrides work with streaming:

```json
{
  "agent": "economist",
  "input": "Explain inflation",
  "model": "gpt-4o",
  "temperature": 0.5
}
```

## Related Documentation

- [LLM Providers](./LLM_PROVIDERS.md)
- [Routing Policies](./ROUTING_POLICIES.md)
- [Cost Control](./COST_CONTROL.md)
- [Streaming Chat](./STREAMING_CHAT.md)

