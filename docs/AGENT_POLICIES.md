# Agent Policies Guide

This guide explains how to create and manage agent policies using YAML.

## Overview

Agent policies define agent behavior, personality, knowledge base configuration, and capabilities. They are stored as YAML files in the `agents/policies/` directory.

## Policy Structure

```yaml
version: "1.0.0"
agent:
  name: "agent-name"
  display_name: "Agent Display Name"
  description: "Brief description"
  
  personality: |
    Detailed personality description.
    This is what defines how the agent behaves.
  
  knowledge_base:
    enabled: true
    vector_db:
      type: "qdrant"
      collection: "agent_kb"
      top_k: 5
      similarity_threshold: 0.7
    documents:
      type: "local"
      paths:
        - "path/to/document.md"
  
  behavior:
    temperature: 0.3
    max_tokens: 2000
    response_style: "professional"
    tone: "professional"
  
  capabilities:
    - "capability1"
    - "capability2"
  
  constraints:
    - "Constraint 1"
    - "Constraint 2"
  
  metadata:
    category: "category"
    tags: ["tag1", "tag2"]
```

## Creating a New Agent Policy

1. **Create YAML file**: `agents/policies/my-agent.yaml`

2. **Define basic info**:
```yaml
version: "1.0.0"
agent:
  name: "my-agent"
  display_name: "My Custom Agent"
  description: "A custom agent for specific tasks"
```

3. **Add personality**:
```yaml
  personality: |
    You are a helpful assistant specialized in [domain].
    Provide clear, actionable advice.
```

4. **Configure knowledge base** (optional):
```yaml
  knowledge_base:
    enabled: true
    vector_db:
      type: "qdrant"
      collection: "my_agent_kb"
      top_k: 5
    documents:
      type: "local"
      paths:
        - "knowledge/my-domain/docs.md"
```

5. **Set behavior**:
```yaml
  behavior:
    temperature: 0.3
    max_tokens: 2000
    response_style: "professional"
    tone: "friendly"
```

## Knowledge Base Configuration

### Vector Database

Supported types:
- `qdrant` (default, recommended)
- `chroma` (embedded, for development)
- `pinecone` (cloud)
- `weaviate` (enterprise)
- `custom` (via plugin)

Example:
```yaml
vector_db:
  type: "qdrant"
  collection: "agent_kb"
  top_k: 5
  similarity_threshold: 0.7
  config:
    host: "${VECTOR_DB_HOST}"
    port: "${VECTOR_DB_PORT}"
```

### Document Storage

Supported types:
- `local` (filesystem)
- `s3` (AWS S3 or compatible)
- `azure` (Azure Blob Storage)
- `gcs` (Google Cloud Storage)
- `custom` (via plugin)

Example:
```yaml
documents:
  type: "local"
  paths:
    - "knowledge/domain/docs.md"
    - "knowledge/domain/guides.md"
```

## Behavior Settings

- **temperature**: 0.0-2.0 (creativity, default: 0.3)
- **max_tokens**: Maximum response length (default: 2000)
- **response_style**: analytical, strategic, pragmatic, advisory
- **tone**: professional, casual, friendly

## Capabilities and Constraints

**Capabilities**: List of what the agent can do
```yaml
capabilities:
  - "market_analysis"
  - "risk_assessment"
```

**Constraints**: Rules the agent must follow
```yaml
constraints:
  - "Always cite sources"
  - "Provide quantitative analysis"
```

## Hot Reload

Policies are loaded on startup. To reload without restart:

```python
from app.agents.policy import get_policy_loader

policy_loader = get_policy_loader()
policy_loader.reload()
```

Or via API endpoint (future feature).

## Validation

Policies are validated on load:
- Required fields: `name`, `personality`
- Valid types for vector_db and documents
- Valid behavior settings

## Examples

See existing policies:
- `agents/policies/economist.yaml`
- `agents/policies/strategist.yaml`
- `agents/policies/entrepreneur.yaml`
- `agents/policies/startup.yaml`

## Best Practices

1. **Version your policies**: Use semantic versioning
2. **Keep personalities focused**: Clear, specific descriptions
3. **Use knowledge base**: Enable RAG for domain-specific agents
4. **Set appropriate constraints**: Guide agent behavior
5. **Test thoroughly**: Validate policies before production

## Troubleshooting

**Policy not loading**:
- Check YAML syntax
- Verify file is in `agents/policies/`
- Check logs for validation errors

**RAG not working**:
- Verify vector DB is running (Qdrant)
- Check collection exists
- Verify document paths are correct

**Custom provider not found**:
- Check plugin path in environment
- Verify plugin file naming: `vector_db_{name}.py`
- Check plugin class naming: `{Name}Provider`


