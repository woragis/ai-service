# Model Selection & Routing Policies

## Overview

The AI service uses intelligent routing policies to automatically select the best LLM provider and model based on query complexity, cost preferences, and quality requirements.

## Features

### 1. Provider Preference Rules

Configure which providers to use and in what order.

#### Configuration

```yaml
routing:
  providers:
    openai:
      enabled: true
      priority: 1
      models:
        - name: "gpt-4o-mini"
          cost_per_million_input_tokens: 0.15
          cost_per_million_output_tokens: 0.60
          quality_score: 8
          complexity_threshold: "medium"
        - name: "gpt-4o"
          cost_per_million_input_tokens: 5.00
          cost_per_million_output_tokens: 15.00
          quality_score: 10
          complexity_threshold: "complex"
      fallback_to: ["anthropic", "xai"]
```

### 2. Fallback Chains

Automatic provider switching when primary provider fails.

#### Configuration

```yaml
routing:
  providers:
    openai:
      fallback_to: ["anthropic", "xai"]
    anthropic:
      fallback_to: ["openai", "xai"]
```

#### How It Works

1. Try primary provider
2. On failure, try first fallback
3. Continue through chain until success
4. If all fail, return error

### 3. Query Complexity Detection

Automatically detects query complexity and selects appropriate model.

#### Complexity Levels

- **Simple**: Short queries, basic questions
- **Medium**: Moderate length, some analysis needed
- **Complex**: Long queries, deep analysis, multi-step reasoning

#### Detection Logic

```python
def detect_query_complexity(query: str) -> str:
    word_count = len(query.split())
    if word_count < 15:
        return "simple"
    elif word_count < 50:
        return "medium"
    else:
        return "complex"
```

#### Model Selection

- Simple queries → Use cheaper models (gpt-4o-mini, claude-haiku)
- Medium queries → Use balanced models
- Complex queries → Use high-quality models (gpt-4o, claude-opus)

### 4. Cost vs Quality Trade-offs

Three cost modes for different use cases:

#### Cost Modes

1. **cost_optimized**: Prioritize cheapest models
2. **balanced**: Balance cost and quality (default)
3. **quality_optimized**: Prioritize best quality models

#### Configuration

```yaml
routing:
  default_cost_mode: "balanced"
  cost_quality:
    mode: "balanced"
    provider_mapping:
      cost_optimized:
        xai: "grok-1"
        openai: "gpt-4o-mini"
      quality_optimized:
        openai: "gpt-4o"
        anthropic: "claude-3-opus"
```

## Usage

### Automatic Routing

```python
from app.routing import select_provider_and_model

provider, model, fallback_chain = select_provider_and_model(
    requested_provider=None,  # Auto-select
    requested_model=None,     # Auto-select
    query="What is the meaning of life?",
    agent_name="philosopher",
    cost_mode="balanced",
    enable_fallback=True
)
```

### Explicit Provider/Model

```python
provider, model, fallback_chain = select_provider_and_model(
    requested_provider="openai",
    requested_model="gpt-4o",
    query="Complex analysis needed",
    agent_name="analyst",
    cost_mode="quality_optimized",
    enable_fallback=True
)
```

### With Fallback Execution

```python
from app.routing import execute_with_fallback

result = await execute_with_fallback(
    provider="openai",
    model="gpt-4o",
    fallback_chain=["anthropic", "xai"],
    execute_fn=your_chat_function,
    endpoint="/v1/chat"
)
```

## Configuration Examples

### Cost-Optimized Setup

```yaml
routing:
  default_cost_mode: "cost_optimized"
  providers:
    xai:
      priority: 1
      models:
        - name: "grok-1"
          complexity_threshold: "simple"
    openai:
      priority: 2
      models:
        - name: "gpt-4o-mini"
          complexity_threshold: "medium"
```

### Quality-Optimized Setup

```yaml
routing:
  default_cost_mode: "quality_optimized"
  providers:
    openai:
      priority: 1
      models:
        - name: "gpt-4o"
          complexity_threshold: "complex"
    anthropic:
      priority: 2
      models:
        - name: "claude-3-opus"
          complexity_threshold: "complex"
```

### Balanced Setup (Default)

```yaml
routing:
  default_cost_mode: "balanced"
  providers:
    openai:
      priority: 1
      models:
        - name: "gpt-4o-mini"  # For simple/medium
          complexity_threshold: "medium"
        - name: "gpt-4o"       # For complex
          complexity_threshold: "complex"
```

## Environment Variables

Set default cost mode:

```bash
export COST_MODE=balanced  # or cost_optimized, quality_optimized
```

## Hot Reload

Reload routing policies without restarting:

```bash
curl -X POST http://localhost:8000/v1/routing/reload
```

## Monitoring

Routing decisions are logged:

- `Auto-selected provider/model` - Automatic selection
- `Explicit provider/model selected` - User-specified
- `Fallback provider succeeded` - Fallback used

## Best Practices

1. **Configure Multiple Providers**
   - Redundancy for high availability
   - Cost optimization options
   - Quality tier options

2. **Set Appropriate Complexity Thresholds**
   - Match models to query types
   - Avoid over-provisioning
   - Avoid under-provisioning

3. **Use Fallback Chains**
   - Always configure fallbacks
   - Order by preference
   - Include cost-effective options

4. **Monitor Routing Decisions**
   - Track which providers/models are used
   - Adjust based on real usage
   - Optimize for cost/quality balance

5. **Test Different Cost Modes**
   - Verify cost_optimized saves money
   - Verify quality_optimized meets requirements
   - Use balanced as default

## Related Documentation

- [Retry & Resilience Policies](./RETRY_RESILIENCE.md)
- [Cost Control Policies](./COST_CONTROL.md)
- [Circuit Breakers](./CIRCUIT_BREAKERS.md)

