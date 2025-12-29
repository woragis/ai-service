# Feature Flag Policies

## Overview

The AI service uses feature flags to enable/disable features dynamically without code changes or service restarts.

## Features

### 1. RAG Enable/Disable

Control RAG (Retrieval-Augmented Generation) per agent.

#### Configuration

```yaml
features:
  rag:
    enabled: true
    default_enabled: true
    per_agent_enabled:
      economist: true
      strategist: true
      developer: true
      entrepreneur: false  # Disable for entrepreneur
      startup: true
```

#### Usage

RAG is automatically checked before retrieval:

```python
from app.features import is_rag_enabled

if is_rag_enabled(agent_name):
    rag_context = await get_rag_context(agent_name, query)
```

### 2. Streaming Enable/Disable

Control streaming per endpoint.

#### Configuration

```yaml
features:
  streaming:
    enabled: true
    per_endpoint_enabled:
      /v1/chat/stream: true
      /v1/chat: false
```

#### Usage

Streaming is checked before processing:

```python
from app.features import is_streaming_enabled

if not is_streaming_enabled("/v1/chat/stream"):
    raise HTTPException(status_code=400, detail="Streaming disabled")
```

### 3. Provider Enable/Disable

Control which providers are available.

#### Configuration

```yaml
features:
  providers:
    enabled_providers: ["openai", "anthropic", "cipher", "xai"]
    disabled_providers: []  # Explicitly disabled
```

#### Usage

Providers are checked before routing:

```python
from app.features import is_provider_enabled

if not is_provider_enabled("openai"):
    raise HTTPException(status_code=400, detail="Provider disabled")
```

### 4. Custom Feature Flags

Define and use custom feature flags.

#### Configuration

```yaml
features:
  custom_flags:
    advanced_logging: true
    experimental_features: false
    beta_agents: true
```

#### Usage

```python
from app.features import is_feature_enabled

if is_feature_enabled("experimental_features"):
    # Use experimental feature
    pass
```

## Usage

### Check Feature Status

```bash
curl http://localhost:8000/v1/features/config
```

Response:
```json
{
  "rag": {
    "enabled": true,
    "default_enabled": true,
    "per_agent_enabled": {
      "economist": true,
      "entrepreneur": false
    }
  },
  "streaming": {
    "enabled": true,
    "per_endpoint_enabled": {
      "/v1/chat/stream": true
    }
  },
  "providers": {
    "enabled_providers": ["openai", "anthropic"],
    "disabled_providers": []
  },
  "custom_flags": {
    "advanced_logging": true
  }
}
```

## Use Cases

### Gradual Feature Rollout

1. Enable feature for specific agents
2. Monitor performance
3. Gradually expand to more agents
4. Enable globally when stable

### A/B Testing

```yaml
features:
  custom_flags:
    new_routing_algorithm: true  # For test group
```

### Emergency Disable

Quickly disable features without code changes:

```yaml
features:
  streaming:
    enabled: false  # Disable all streaming
  providers:
    disabled_providers: ["openai"]  # Disable problematic provider
```

### Cost Control

Disable expensive features:

```yaml
features:
  rag:
    per_agent_enabled:
      developer: false  # Disable RAG for cost savings
```

## Best Practices

1. **Use Feature Flags for New Features**
   - Enable gradually
   - Easy rollback
   - Test in production safely

2. **Monitor Feature Usage**
   - Track which features are enabled
   - Monitor performance impact
   - Adjust based on data

3. **Document Custom Flags**
   - Document what each flag does
   - Note dependencies
   - Include removal plan

4. **Clean Up Unused Flags**
   - Remove flags after feature is stable
   - Keep config clean
   - Avoid flag proliferation

5. **Test Flag Combinations**
   - Test with different flag states
   - Verify no conflicts
   - Ensure graceful degradation

## Hot Reload

Reload feature flags:

```bash
curl -X POST http://localhost:8000/v1/features/reload
```

## Configuration Examples

### Development Environment

```yaml
features:
  rag:
    enabled: true
    default_enabled: true
  streaming:
    enabled: true
  providers:
    enabled_providers: ["openai", "anthropic", "cipher", "xai"]
  custom_flags:
    debug_mode: true
    experimental_features: true
```

### Production Environment

```yaml
features:
  rag:
    enabled: true
    default_enabled: false  # Opt-in per agent
    per_agent_enabled:
      economist: true
      strategist: true
  streaming:
    enabled: true
  providers:
    enabled_providers: ["openai", "anthropic"]  # Only stable providers
  custom_flags:
    debug_mode: false
    experimental_features: false
```

### Cost-Optimized

```yaml
features:
  rag:
    enabled: false  # Disable RAG to save costs
  streaming:
    enabled: false  # Disable streaming
  providers:
    enabled_providers: ["xai"]  # Only cheapest provider
```

## Related Documentation

- [Agent Policies](./AGENT_POLICIES.md)
- [RAG & Knowledge Base](./VECTOR_DB_OPTIONS.md)
- [Model Selection & Routing](./ROUTING_POLICIES.md)

