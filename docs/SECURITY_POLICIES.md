# Security & Content Policies

## Overview

The AI service implements comprehensive security measures to protect against attacks, detect sensitive information, and sanitize content before returning to users.

## Features

### 1. Content Filtering

Block dangerous content patterns and keywords.

#### Configuration

```yaml
security:
  content_filter:
    enabled: true
    blocked_patterns:
      - "<script[^>]*>.*?</script>"  # XSS attempts
      - "javascript:"                # JavaScript protocol
      - "on\\w+\\s*="                # Event handlers
      - "eval\\s*\\("                 # eval() calls
    blocked_keywords:
      - "malware"
      - "virus"
      - "exploit"
    action: "block"  # Options: block, warn, sanitize
```

#### Actions

- **block**: Reject request immediately
- **warn**: Log warning but allow
- **sanitize**: Remove dangerous content

### 2. PII Detection and Masking

Detect and mask personally identifiable information.

#### Supported PII Types

- **Email Addresses**: `user@example.com` → `u***@example.com`
- **Phone Numbers**: `+1-555-123-4567` → `***-***-4567`
- **SSN**: `123-45-6789` → `XXX-XX-6789`
- **Credit Cards**: `1234-5678-9012-3456` → `****-****-****-3456`
- **IP Addresses**: `192.168.1.1` → `XXX.XXX.XXX.1`

#### Configuration

```yaml
security:
  pii_detection:
    enabled: true
    detect_email: true
    detect_phone: true
    detect_ssn: true
    detect_credit_card: true
    detect_ip_address: true
    mask_char: "*"
    action: "mask"  # Options: mask, block, warn
```

### 3. Response Sanitization

Remove potentially dangerous content from responses.

#### Configuration

```yaml
security:
  response_sanitization:
    enabled: true
    remove_html_tags: true
    remove_script_tags: true
    remove_event_handlers: true
    max_length: null  # null = no limit
    allowed_html_tags: ["p", "br", "strong", "em"]
```

#### Sanitization Steps

1. Remove script tags
2. Remove event handlers (onclick, etc.)
3. Remove HTML tags (except allowed)
4. Truncate if exceeds max_length

### 4. Prompt Injection Detection

Detect and prevent prompt injection attacks.

#### Configuration

```yaml
security:
  prompt_injection:
    enabled: true
    suspicious_patterns:
      - "ignore\\s+(previous|above|all)\\s+instructions?"
      - "forget\\s+(everything|all|previous)"
      - "you\\s+are\\s+now\\s+(a|an)\\s+"
      - "system\\s*:\\s*"
      - "<\\|system\\|>"
    action: "block"
    threshold: 0.5
```

#### Detection Logic

- Pattern matching against suspicious phrases
- Confidence scoring based on matches
- Action taken if confidence > threshold

## Usage

### Automatic Application

Security checks are automatically applied:

1. **Input Validation** (before processing):
   - Prompt injection detection
   - Content filtering
   - PII detection and masking

2. **Output Sanitization** (before returning):
   - Response sanitization
   - PII masking
   - Content filtering

### Manual Checks

```python
from app.security import (
    check_prompt_injection,
    check_content_filter,
    check_pii,
    mask_pii,
    sanitize_response
)

# Check prompt injection
allowed, error = check_prompt_injection(user_input)
if not allowed:
    raise HTTPException(status_code=400, detail=error)

# Check content filter
allowed, error = check_content_filter(user_input)
if not allowed:
    raise HTTPException(status_code=400, detail=error)

# Check and mask PII
allowed, error, counts = check_pii(user_input)
if counts:
    masked_input, _ = mask_pii(user_input)

# Sanitize response
clean_response = sanitize_response(llm_response)
```

## Monitoring

### Logging

Security events are logged:

- `Content blocked by keyword` - Dangerous keyword detected
- `Prompt injection detected` - Injection attempt blocked
- `PII masked in input/response` - PII detected and masked
- `Response truncated` - Response exceeded max_length

### Metrics

Track security events via Prometheus (if implemented):
- Blocked requests count
- PII detection count
- Prompt injection attempts

## Best Practices

1. **Keep Patterns Updated**
   - Add new attack patterns as discovered
   - Review and update regularly
   - Test against known attacks

2. **Configure PII Detection**
   - Enable for all sensitive data types
   - Use masking (not blocking) for most cases
   - Block only for highly sensitive scenarios

3. **Set Appropriate Thresholds**
   - Lower threshold = more false positives
   - Higher threshold = more false negatives
   - Test with real queries

4. **Sanitize All Responses**
   - Never trust LLM output
   - Remove all dangerous content
   - Keep only safe HTML tags

5. **Monitor Security Events**
   - Track blocked requests
   - Alert on suspicious patterns
   - Review logs regularly

## Hot Reload

Reload security policies:

```bash
curl -X POST http://localhost:8000/v1/security/reload
```

## Configuration Examples

### Strict Security

```yaml
security:
  content_filter:
    action: "block"
    blocked_keywords: ["malware", "virus", "exploit", "hack"]
  pii_detection:
    action: "block"  # Block instead of mask
  prompt_injection:
    threshold: 0.3  # Lower threshold = more sensitive
```

### Balanced Security

```yaml
security:
  content_filter:
    action: "sanitize"  # Remove instead of block
  pii_detection:
    action: "mask"  # Mask instead of block
  prompt_injection:
    threshold: 0.5  # Default threshold
```

### Permissive (Development)

```yaml
security:
  content_filter:
    enabled: false
  pii_detection:
    action: "warn"  # Warn but allow
  prompt_injection:
    action: "warn"
```

## Related Documentation

- [Security Testing](./security-testing.md)
- [Quality & Validation Policies](./QUALITY_POLICIES.md)
- [Request Timeouts](./request-timeouts.md)

