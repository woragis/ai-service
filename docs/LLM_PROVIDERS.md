# LLM Providers

## Overview

The AI service supports multiple Large Language Model (LLM) providers, allowing you to choose the best model for each use case or automatically route requests based on policies.

## Supported Providers

### 1. OpenAI (ChatGPT)

**Models:**
- `gpt-4o` - Latest GPT-4 model, high quality
- `gpt-4o-mini` - Faster, cost-effective option
- `gpt-4-turbo` - Previous generation
- `gpt-3.5-turbo` - Legacy model

**Configuration:**
```bash
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
```

**Usage:**
```python
from app.providers import make_model

model = make_model("openai", "gpt-4o", temperature=0.3)
```

### 2. Anthropic (Claude)

**Models:**
- `claude-3-5-sonnet-latest` - Latest Claude 3.5 Sonnet
- `claude-3-opus-20240229` - High quality, slower
- `claude-3-sonnet-20240229` - Balanced quality/speed
- `claude-3-haiku-20240307` - Fast, cost-effective

**Configuration:**
```bash
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

**Usage:**
```python
model = make_model("anthropic", "claude-3-5-sonnet-latest", temperature=0.3)
```

### 3. xAI (Grok)

**Models:**
- `grok-beta` - Grok beta model

**Configuration:**
```bash
XAI_API_KEY=your-api-key
XAI_BASE_URL=https://api.x.ai/v1
XAI_MODEL=grok-beta
```

**Usage:**
```python
model = make_model("xai", "grok-beta", temperature=0.3)
```

### 4. Cipher (NoFilterGPT)

**Features:**
- Chat completions
- Image generation
- No content filtering

**Configuration:**
```bash
CIPHER_API_KEY=your-api-key
CIPHER_BASE_URL=https://api.nofiltergpt.com/v1/chat/completions
CIPHER_MAX_TOKENS=800
CIPHER_TOP_P=1.0
CIPHER_IMAGE_URL=https://api.nofiltergpt.com/v1/images/generations
```

**Usage:**
```python
from app.providers import CipherClient

client = CipherClient.from_env()
response = await client.chat(messages=[...], temperature=0.3, max_tokens=800, top_p=1.0)
```

### 5. Manus

**Configuration:**
```bash
MANUS_API_KEY=your-api-key
MANUS_BASE_URL=https://your-manus-endpoint.com
MANUS_MODEL=manus-chat
```

**Usage:**
```python
model = make_model("manus", "manus-chat", temperature=0.3)
```

## Provider Selection

### Automatic Selection

Providers are automatically selected based on routing policies:

```yaml
routing:
  providers:
    openai:
      priority: 1
      enabled: true
    anthropic:
      priority: 2
      enabled: true
```

See [Routing Policies](./ROUTING_POLICIES.md) for details.

### Manual Selection

Specify provider in API request:

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "input": "Hello"
}
```

### Fallback Chains

If a provider fails, the system automatically falls back to the next provider in the chain:

```yaml
routing:
  providers:
    openai:
      fallback_to: ["anthropic", "xai"]
```

## Provider Comparison

| Provider | Speed | Quality | Cost | Best For |
|----------|-------|---------|------|----------|
| OpenAI GPT-4o | Fast | High | Medium | General purpose |
| OpenAI GPT-4o-mini | Very Fast | Good | Low | High volume, simple tasks |
| Anthropic Claude 3.5 | Medium | Very High | High | Complex reasoning |
| Anthropic Claude Haiku | Fast | Good | Low | Cost-sensitive |
| xAI Grok | Fast | Good | Low | Cost optimization |
| Cipher | Fast | Variable | Low | Unfiltered content |

## Cost Considerations

Provider costs vary significantly:

- **OpenAI GPT-4o-mini**: ~$0.15/$0.60 per million tokens (input/output)
- **OpenAI GPT-4o**: ~$5.00/$15.00 per million tokens
- **Anthropic Claude 3.5 Sonnet**: ~$3.00/$15.00 per million tokens
- **Anthropic Claude Haiku**: ~$0.25/$1.25 per million tokens
- **xAI Grok**: ~$0.10/$0.50 per million tokens

Use cost-based routing to optimize spending. See [Cost Control Policies](./COST_CONTROL.md).

## Feature Support

| Feature | OpenAI | Anthropic | xAI | Cipher | Manus |
|---------|--------|-----------|-----|--------|-------|
| Chat | ✅ | ✅ | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ | ❌ | ✅ |
| Images | ✅ | ❌ | ❌ | ✅ | ❌ |
| Function Calling | ✅ | ✅ | ❌ | ❌ | ❌ |

## Best Practices

1. **Use Multiple Providers** - Redundancy and cost optimization
2. **Configure Fallbacks** - Automatic failover on errors
3. **Monitor Costs** - Track spending per provider
4. **Match Model to Task** - Use appropriate model for complexity
5. **Enable Circuit Breakers** - Prevent cascading failures

## Related Documentation

- [Routing Policies](./ROUTING_POLICIES.md)
- [Cost Control Policies](./COST_CONTROL.md)
- [Circuit Breakers](./CIRCUIT_BREAKERS.md)
- [Retry & Resilience](./RETRY_RESILIENCE.md)

