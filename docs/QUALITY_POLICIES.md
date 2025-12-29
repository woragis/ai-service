# Quality & Validation Policies

## Overview

The AI service implements quality checks and validation to ensure responses meet standards for length, format, coherence, relevance, and safety.

## Features

### 1. Response Length Limits

Enforce minimum and maximum response lengths.

#### Configuration

```yaml
quality:
  length_limits:
    enabled: true
    min_length: 10
    max_length: 50000
    per_agent_limits:
      developer:
        min: 50
        max: 20000
      economist:
        min: 100
        max: 30000
```

#### Validation

- Minimum length prevents empty/too-short responses
- Maximum length prevents excessive output
- Per-agent limits for different use cases

### 2. Output Format Validation

Validate response format (JSON, Markdown, text).

#### Configuration

```yaml
quality:
  format_validation:
    enabled: true
    allowed_formats: ["text", "json", "markdown"]
    required_format: null  # null = any allowed format
    validate_json: true
    validate_markdown: false
```

#### Format Detection

- **JSON**: Detects JSON structure, validates syntax
- **Markdown**: Detects markdown patterns, validates structure
- **Text**: Default format for plain text

### 3. Quality Checks

Evaluate response quality (coherence and relevance).

#### Coherence Scoring

Measures how coherent the response is:
- Sentence length variation
- Word repetition
- Overall structure

#### Relevance Scoring

Measures how relevant response is to query:
- Keyword overlap
- Semantic similarity (if enabled)
- Query matching

#### Configuration

```yaml
quality:
  quality_checks:
    enabled: true
    check_coherence: true
    check_relevance: true
    coherence_threshold: 0.5
    relevance_threshold: 0.5
    use_semantic_similarity: true
```

### 4. Toxicity Detection

Detect toxic or harmful content in responses.

#### Configuration

```yaml
quality:
  toxicity_detection:
    enabled: true
    threshold: 0.7
    action: "block"  # Options: block, warn, sanitize
    toxic_keywords:
      - "hate"
      - "violence"
      - "discrimination"
      - "harassment"
```

#### Detection Method

- Keyword matching
- Pattern matching for aggressive language
- Confidence scoring

## Usage

### Automatic Validation

Quality checks are automatically applied before returning responses:

1. Validate length
2. Validate format
3. Check quality (coherence/relevance)
4. Check toxicity
5. Return or reject based on results

### Manual Validation

```python
from app.quality import (
    validate_length,
    validate_format,
    validate_quality,
    check_toxicity
)

# Validate length
valid, error = validate_length(response, agent_name="developer")
if not valid:
    raise HTTPException(status_code=500, detail=error)

# Validate format
valid, error, format_type = validate_format(response)
if not valid:
    raise HTTPException(status_code=500, detail=error)

# Validate quality
valid, error, scores = validate_quality(query, response, agent_name)
# Logs warning if quality low, doesn't block

# Check toxicity
allowed, error, score = check_toxicity(response)
if not allowed:
    raise HTTPException(status_code=500, detail=error)
```

## Quality Scores

### Coherence Score (0-1)

- **0.0-0.3**: Low coherence (repetitive, fragmented)
- **0.3-0.6**: Moderate coherence
- **0.6-1.0**: High coherence (well-structured)

### Relevance Score (0-1)

- **0.0-0.3**: Low relevance (unrelated to query)
- **0.3-0.6**: Moderate relevance
- **0.6-1.0**: High relevance (directly addresses query)

### Toxicity Score (0-1)

- **0.0-0.5**: Low toxicity
- **0.5-0.7**: Moderate toxicity (warning)
- **0.7-1.0**: High toxicity (blocked if threshold met)

## Monitoring

### Logging

Quality events are logged:

- `Response length validation failed` - Length out of range
- `Format validation failed` - Invalid format
- `Quality check failed` - Low coherence/relevance
- `Content blocked due to toxicity` - Toxic content detected

### Metrics

Track quality metrics via Prometheus (if implemented):
- Average coherence scores
- Average relevance scores
- Toxicity detection rate
- Format validation failures

## Best Practices

1. **Set Appropriate Length Limits**
   - Match to use cases
   - Consider model capabilities
   - Per-agent limits for different needs

2. **Configure Format Validation**
   - Require specific formats when needed
   - Validate JSON for API responses
   - Allow flexibility for general chat

3. **Tune Quality Thresholds**
   - Lower = more strict, more rejections
   - Higher = more lenient, fewer rejections
   - Test with real responses

4. **Update Toxic Keywords**
   - Add new harmful terms
   - Review regularly
   - Consider context (some words OK in context)

5. **Monitor Quality Metrics**
   - Track average scores
   - Identify quality issues
   - Adjust thresholds based on data

## Hot Reload

Reload quality policies:

```bash
curl -X POST http://localhost:8000/v1/quality/reload
```

## Configuration Examples

### Strict Quality

```yaml
quality:
  length_limits:
    min_length: 50
    max_length: 10000
  quality_checks:
    coherence_threshold: 0.7
    relevance_threshold: 0.7
  toxicity_detection:
    threshold: 0.5  # Lower = more sensitive
```

### Balanced Quality

```yaml
quality:
  length_limits:
    min_length: 10
    max_length: 50000
  quality_checks:
    coherence_threshold: 0.5
    relevance_threshold: 0.5
  toxicity_detection:
    threshold: 0.7
```

### Permissive (Development)

```yaml
quality:
  length_limits:
    enabled: false
  quality_checks:
    enabled: false
  toxicity_detection:
    action: "warn"  # Warn but allow
```

## Related Documentation

- [Security & Content Policies](./SECURITY_POLICIES.md)
- [Performance Testing](./performance-testing.md)
- [SLO/SLI Tracking](./slo-sli.md)

