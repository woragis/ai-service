# Agent Auto-Selection

## Overview

The AI service supports automatic agent selection based on query content. When `"agent": "auto"` is specified, the system analyzes the query and selects the most appropriate agent persona.

## How It Works

The auto-selection algorithm uses keyword matching to identify the best agent:

```python
def pick_agent_auto(text: str) -> str:
    lowered = text.lower()
    
    # Check for keywords specific to each agent
    if any(k in lowered for k in ["market", "inflation", "macro", "econom", "unit economics", "pricing"]):
        return "economist"
    elif any(k in lowered for k in ["strategy", "plan", "roadmap", "vision", "mission"]):
        return "strategist"
    elif any(k in lowered for k in ["startup", "founder", "funding", "venture", "pitch"]):
        return "startup"
    elif any(k in lowered for k in ["code", "programming", "debug", "algorithm", "function"]):
        return "developer"
    elif any(k in lowered for k in ["marketing", "campaign", "brand", "advertising", "social media"]):
        return "marketer"
    else:
        return "entrepreneur"  # Default fallback
```

## Usage

### API Request

```json
{
  "agent": "auto",
  "input": "What is the current inflation rate in the US?"
}
```

The system will automatically select the "economist" agent based on the "inflation" keyword.

### Examples

| Query | Selected Agent | Reason |
|-------|----------------|--------|
| "What is inflation?" | economist | Contains "inflation" |
| "Create a marketing strategy" | strategist | Contains "strategy" |
| "How to raise funding?" | startup | Contains "funding" |
| "Fix this Python code" | developer | Contains "code" |
| "Plan a social media campaign" | marketer | Contains "marketing", "campaign" |
| "General business question" | entrepreneur | Default fallback |

## Keyword Mapping

### Economist Agent

Keywords: `market`, `inflation`, `macro`, `econom`, `unit economics`, `pricing`

### Strategist Agent

Keywords: `strategy`, `plan`, `roadmap`, `vision`, `mission`

### Startup Agent

Keywords: `startup`, `founder`, `funding`, `venture`, `pitch`

### Developer Agent

Keywords: `code`, `programming`, `debug`, `algorithm`, `function`

### Marketer Agent

Keywords: `marketing`, `campaign`, `brand`, `advertising`, `social media`

### Entrepreneur Agent

Default fallback when no specific keywords match.

## Customization

### Extending Keywords

Modify the `pick_agent_auto` function in `app/main.py`:

```python
def pick_agent_auto(text: str) -> str:
    lowered = text.lower()
    
    # Add custom keywords
    if any(k in lowered for k in ["custom", "keyword", "here"]):
        return "custom_agent"
    
    # ... existing logic
```

### Using ML-Based Selection

For more sophisticated selection, you could:

1. Use embeddings to find semantic similarity
2. Train a classifier on labeled queries
3. Use LLM to classify queries

Example with embeddings:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def pick_agent_ml(query: str) -> str:
    query_embedding = model.encode(query)
    
    # Compare with agent descriptions
    agent_descriptions = {
        "economist": "Expert in economics, markets, inflation, macroeconomics",
        "strategist": "Expert in business strategy, planning, vision",
        # ...
    }
    
    # Find most similar agent
    # ... similarity calculation
    
    return best_agent
```

## Best Practices

1. **Use Specific Queries** - More specific queries lead to better selection
2. **Test Keyword Matching** - Verify keywords match your use cases
3. **Monitor Selection** - Log which agent is selected for analysis
4. **Provide Fallback** - Always have a default agent
5. **Consider Context** - For multi-turn conversations, maintain agent context

## Limitations

- **Keyword-Based**: Simple keyword matching may miss nuanced queries
- **No Context**: Doesn't consider conversation history
- **Static**: Keywords are hardcoded, not learned
- **Ambiguous Queries**: May select wrong agent for ambiguous queries

## Future Enhancements

- ML-based agent selection
- Context-aware selection (consider conversation history)
- Confidence scoring
- User preference learning
- Multi-agent collaboration

## Related Documentation

- [Agent Policies](./AGENT_POLICIES.md)
- [Agent Policy Architecture](./AGENT_POLICY_ARCHITECTURE.md)
- [RAG & Knowledge Base](./VECTOR_DB_OPTIONS.md)

