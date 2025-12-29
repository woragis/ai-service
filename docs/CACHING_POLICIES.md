# Caching Policies

## Overview

The AI service implements intelligent caching to reduce API calls, improve response times, and lower costs by reusing responses for similar queries.

## Features

### 1. In-Memory Response Caching

Cache responses in memory with configurable eviction policies.

#### Eviction Policies

- **LRU (Least Recently Used)**: Evicts least recently accessed entries
- **LFU (Least Frequently Used)**: Evicts least frequently accessed entries
- **FIFO (First In First Out)**: Evicts oldest entries

#### Configuration

```yaml
caching:
  enabled: true
  size_limits:
    max_size_mb: 500
    max_entries: 10000
    eviction_policy: "lru"
```

### 2. Cache TTL (Time To Live)

Configure how long responses are cached.

#### Configuration

```yaml
caching:
  ttl:
    default_ttl_seconds: 3600  # 1 hour default
    per_agent_ttl:
      economist: 7200      # 2 hours
      strategist: 7200     # 2 hours
      developer: 1800      # 30 minutes
    per_endpoint_ttl:
      /v1/chat: 3600
      /v1/chat/stream: 0  # Disable for streaming
```

### 3. Semantic Similarity Caching

Find and reuse responses for semantically similar queries.

#### Configuration

```yaml
caching:
  semantic_similarity:
    enabled: true
    similarity_threshold: 0.85  # 0-1, higher = more similar
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
    max_cache_entries: 10000
```

#### How It Works

1. Generate embedding for query
2. Search cached queries for similar embeddings
3. If similarity > threshold, return cached response
4. Otherwise, process query and cache result

### 4. Cache Size Limits

Automatic eviction when limits are reached.

#### Limits

- **Max Entries**: Maximum number of cached responses
- **Max Size**: Maximum cache size in MB
- **Automatic Eviction**: Removes entries when limits reached

## Usage

### Automatic Caching

Caching is automatically applied in chat endpoints:

1. Check cache before processing
2. If cache hit, return immediately
3. If cache miss, process and store result

### Cache Statistics

```bash
curl http://localhost:8000/v1/cache/stats
```

Response:
```json
{
  "enabled": true,
  "regular_cache": {
    "entries": 1234,
    "max_entries": 10000,
    "size_mb": 45.2,
    "max_size_mb": 500
  },
  "semantic_cache": {
    "entries": 567,
    "max_entries": 10000,
    "similarity_threshold": 0.85,
    "enabled": true
  }
}
```

### Clear Cache

```bash
curl -X POST http://localhost:8000/v1/cache/clear
```

## Cache Key Generation

Cache keys are generated from:
- Endpoint path
- Agent name
- Provider
- Model
- Query text

This ensures:
- Different agents get different caches
- Different providers get different caches
- Exact query matches are found quickly

## Semantic Similarity

### How It Works

1. **Query Embedding**: Convert query to vector using sentence transformers
2. **Similarity Search**: Find cached queries with high cosine similarity
3. **Threshold Check**: Return cached response if similarity > threshold
4. **Cache Storage**: Store new query and response with embedding

### Similarity Threshold

- **0.85 (Default)**: High similarity required, fewer false matches
- **0.70**: More lenient, more cache hits but potential mismatches
- **0.95**: Very strict, only nearly identical queries match

## Performance Impact

### Benefits

- **Reduced API Calls**: Reuse responses for similar queries
- **Faster Responses**: Cache hits return instantly
- **Lower Costs**: Fewer API calls = lower spending
- **Better UX**: Instant responses for cached queries

### Considerations

- **Memory Usage**: Cache consumes RAM
- **Staleness**: Cached responses may be outdated
- **TTL Tuning**: Balance freshness vs. cache hit rate

## Best Practices

1. **Set Appropriate TTLs**
   - Longer for stable information
   - Shorter for dynamic content
   - Per-agent TTLs for different use cases

2. **Configure Size Limits**
   - Based on available memory
   - Monitor cache size
   - Adjust based on usage

3. **Choose Eviction Policy**
   - LRU: Good general purpose
   - LFU: For frequently repeated queries
   - FIFO: Simple, predictable

4. **Tune Similarity Threshold**
   - Higher = fewer false matches, fewer hits
   - Lower = more hits, potential mismatches
   - Test with real queries

5. **Monitor Cache Performance**
   - Track hit rate
   - Monitor memory usage
   - Adjust based on metrics

## Hot Reload

Reload caching policies:

```bash
curl -X POST http://localhost:8000/v1/cache/reload
```

## Configuration Examples

### High Cache Hit Rate

```yaml
caching:
  ttl:
    default_ttl_seconds: 7200  # 2 hours
  semantic_similarity:
    similarity_threshold: 0.80  # More lenient
  size_limits:
    max_entries: 20000
    max_size_mb: 1000
```

### Memory Constrained

```yaml
caching:
  ttl:
    default_ttl_seconds: 1800  # 30 minutes
  size_limits:
    max_entries: 1000
    max_size_mb: 100
    eviction_policy: "lru"
```

### Quality Focused

```yaml
caching:
  ttl:
    default_ttl_seconds: 3600
  semantic_similarity:
    similarity_threshold: 0.90  # Very strict
  size_limits:
    max_entries: 5000
```

## Related Documentation

- [Performance Testing](./performance-testing.md)
- [Cost Control Policies](./COST_CONTROL.md)
- [Model Selection & Routing](./ROUTING_POLICIES.md)

