# Contract Testing Guide

This guide explains contract testing with Pact for AI Service.

## Overview

Contract testing verifies that the service API matches the expected contract defined by consumers. This ensures API changes don't break consumers.

## Implementation

**Location:** `tests/contract/test_pact.py`

**Tool:** Pact (pact-python)

**What it tests:**
- Request/response format
- Status codes
- Headers
- Data types

## How It Works

1. **Consumer Defines Contract**: Expected request/response
2. **Provider Verifies**: Service matches contract
3. **Contract Published**: Shared contract (Pact Broker)
4. **CI/CD Integration**: Tests run automatically

## Test Structure

```python
pact = Consumer('server').has_pact_with(Provider('ai-service'))

(pact
 .given('agent startup exists')
 .upon_receiving('a chat request')
 .with_request(method='POST', path='/v1/chat', ...)
 .will_respond_with(status=200, body={...}))
```

## Running Tests

### Local Execution

```bash
# Install Pact
pip install pact-python

# Run contract tests
pytest tests/contract/ -v
```

### With Pact Broker

```bash
# Publish contracts
pact-publish --broker-base-url=http://pact-broker --consumer-app-version=1.0.0

# Verify contracts
pact-verifier --broker-base-url=http://pact-broker --provider-base-url=http://ai-service
```

## Contract Examples

### Chat Endpoint

```python
expected_response = {
    "agent": Like("startup"),
    "output": Like("This is a test response")
}
```

### Agents Endpoint

```python
expected_response = EachLike("startup")
```

### Health Endpoint

```python
expected_response = {
    "status": Like("healthy"),
    "service": Like("ai-service"),
    "checks": EachLike({"name": Like("service"), "status": Like("ok")})
}
```

## CI/CD Integration

Add to CI/CD pipeline:

```yaml
contract-tests:
  name: Contract Tests
  runs-on: ubuntu-latest
  steps:
    - name: Run contract tests
      run: pytest tests/contract/ -v
    - name: Publish contracts
      run: pact-publish --broker-base-url=$PACT_BROKER_URL
```

## Best Practices

1. **Version Contracts**: Version contracts with API versions
2. **Test Regularly**: Run contract tests in CI/CD
3. **Update Contracts**: Update when API changes
4. **Use Pact Broker**: Share contracts between teams
5. **Document Changes**: Document breaking changes

## Troubleshooting

### Contract Mismatches

1. Review expected vs. actual response
2. Check data types
3. Verify status codes
4. Check headers

### Pact Broker Issues

1. Verify broker URL
2. Check authentication
3. Verify network connectivity
4. Review broker logs

## References

- [Pact Python](https://pact-foundation.github.io/pact-python/)
- [Pact Documentation](https://docs.pact.io/)

