# Streaming Chat

## Overview

The AI service supports streaming chat responses for real-time user experience. Responses are sent as Server-Sent Events (SSE) as they are generated.

## Endpoint

```
POST /v1/chat/stream
```

## Request

```json
{
  "agent": "economist",
  "input": "Explain inflation",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "system": "You are a helpful assistant",
  "temperature": 0.3
}
```

### Parameters

Same as `/v1/chat` endpoint:
- **agent** (required): Agent persona name or "auto"
- **input** (required): User query
- **provider** (optional): LLM provider
- **model** (optional): Model name
- **system** (optional): System prompt
- **temperature** (optional): Temperature (0.0-2.0)

## Response Format

Server-Sent Events (SSE) stream:

```
data: {"chunk": "Inflation", "done": false}

data: {"chunk": " is", "done": false}

data: {"chunk": " a", "done": false}

data: {"chunk": " general", "done": false}

data: {"chunk": " increase", "done": false}

data: {"chunk": " in", "done": false}

data: {"chunk": " prices", "done": true}
```

### Chunk Format

Each chunk is a JSON object:

```json
{
  "chunk": "text content",
  "done": false
}
```

- **chunk**: Text content of this chunk
- **done**: `true` when stream is complete, `false` otherwise

## Usage Examples

### Python (httpx)

```python
import httpx

with httpx.stream(
    "POST",
    "http://localhost:8000/v1/chat/stream",
    json={
        "agent": "economist",
        "input": "Explain inflation"
    }
) as response:
    for line in response.iter_lines():
        if line.startswith("data: "):
            data = json.loads(line[6:])
            print(data["chunk"], end="", flush=True)
            if data["done"]:
                print()  # New line when done
```

### JavaScript (Fetch API)

```javascript
const response = await fetch('http://localhost:8000/v1/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    agent: 'economist',
    input: 'Explain inflation'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      process.stdout.write(data.chunk);
      if (data.done) {
        console.log(); // New line when done
        break;
      }
    }
  }
}
```

### cURL

```bash
curl -X POST http://localhost:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "economist",
    "input": "Explain inflation"
  }' \
  --no-buffer
```

## Features

### Automatic Agent Selection

Use `"agent": "auto"` for automatic agent selection:

```json
{
  "agent": "auto",
  "input": "What is the current inflation rate?"
}
```

### Provider Selection

Streaming works with all supported providers:

- OpenAI (GPT models)
- Anthropic (Claude models)
- xAI (Grok)
- Manus

Note: Cipher does not support streaming.

### Routing Policies

Streaming requests use the same routing policies as regular chat:

- Automatic provider/model selection
- Fallback chains
- Cost-based routing
- Circuit breakers

## Configuration

### Feature Flags

Control streaming per endpoint:

```yaml
features:
  streaming:
    enabled: true
    per_endpoint_enabled:
      /v1/chat/stream: true
```

### Timeouts

Streaming has longer timeout (5 minutes by default):

```python
ENDPOINT_TIMEOUTS = {
    "/v1/chat/stream": 300,  # 5 minutes
}
```

## Error Handling

### Connection Errors

If connection is lost, the stream will end. Check `done` flag:

```python
if data["done"]:
    # Stream completed successfully
    break
```

### Provider Errors

Errors are sent as JSON in the stream:

```
data: {"error": "Provider error", "detail": "Rate limit exceeded"}
```

## Best Practices

1. **Handle Chunks Incrementally** - Process chunks as they arrive
2. **Check Done Flag** - Always check if stream is complete
3. **Handle Errors** - Check for error messages in stream
4. **Set Appropriate Timeouts** - Streaming can take longer
5. **Use Appropriate Models** - Some models stream faster than others

## Performance

### Latency

- **First Token**: Typically 200-500ms
- **Subsequent Tokens**: 50-200ms per chunk
- **Total Time**: Depends on response length

### Throughput

- **Tokens per Second**: Varies by provider/model
- **GPT-4o-mini**: ~50-100 tokens/second
- **Claude 3.5**: ~30-60 tokens/second

## Limitations

- Cipher provider does not support streaming
- Longer timeout required (5 minutes)
- No caching (streaming responses are not cached)
- Higher resource usage (connection stays open)

## Related Documentation

- [Chat Endpoint](./README.md)
- [LLM Providers](./LLM_PROVIDERS.md)
- [Feature Flags](./FEATURE_FLAGS.md)
- [Request Timeouts](./request-timeouts.md)

