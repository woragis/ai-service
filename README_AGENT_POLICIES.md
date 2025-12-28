# Agent Policies System

## Quick Start

The AI Service now supports YAML-based agent policies with RAG (Retrieval-Augmented Generation) integration.

### Features

✅ **YAML Policies** - Define agents in YAML files
✅ **RAG Support** - Vector database + document retrieval
✅ **Qdrant Integration** - Default vector DB (production-ready)
✅ **Flexible Storage** - Local, S3, Azure, GCS, or custom
✅ **Plugin System** - Custom vector DB and file storage implementations
✅ **Hot Reload** - Update policies without restart

### Running with Docker Compose

```bash
# Start Qdrant + AI Service
docker-compose up -d

# Or for testing
docker-compose -f docker-compose.test.yml up -d
```

### Creating an Agent Policy

1. Create `agents/policies/my-agent.yaml`:

```yaml
version: "1.0.0"
agent:
  name: "my-agent"
  display_name: "My Custom Agent"
  personality: |
    You are a helpful assistant specialized in [domain].
    Provide clear, actionable advice.
  
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
  
  behavior:
    temperature: 0.3
    max_tokens: 2000
```

2. Add documents to `knowledge/` directory
3. Restart service (or use hot reload)

### User Custom Policies

Users can provide their own policies via volume mount:

```yaml
volumes:
  - ./user-policies:/app/agents/policies
```

The service will load all `.yaml` files from the policies directory.

### Custom Vector DB / File Storage

Users can provide custom implementations via plugins:

1. Create plugin file: `plugins/vector_db_custom.py`
2. Implement `VectorDBProvider` interface
3. Set environment: `VECTOR_DB_TYPE=custom`

See `docs/AGENT_POLICY_ARCHITECTURE.md` for details.

## Documentation

- [Agent Policies Guide](./docs/AGENT_POLICIES.md)
- [Architecture](./docs/AGENT_POLICY_ARCHITECTURE.md)
- [Vector DB Options](./docs/VECTOR_DB_OPTIONS.md)

