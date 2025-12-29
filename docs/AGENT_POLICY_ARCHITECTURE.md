# Agent Policy Architecture

This document describes the YAML-based agent policy system with knowledge base integration.

## Overview

Agents are defined via YAML policies that include:
- Personality and behavior
- Knowledge base configuration (vector DB + documents)
- Capabilities and constraints
- User-customizable policies

## YAML Policy Structure

```yaml
# agents/policies/economist.yaml
version: "1.0.0"
agent:
  name: "economist"
  display_name: "Economist Agent"
  description: "A seasoned macro- and micro-economist"
  
  personality: |
    A seasoned macro- and micro-economist. Analyze markets, policy impacts,
    unit economics, and risks. Support with data references when possible.
    Be concise, structured, and provide actionable insights.
    When assumptions are needed, state them explicitly.
  
  # Knowledge base configuration
  knowledge_base:
    enabled: true
    
    # Vector database configuration
    vector_db:
      type: "chroma"  # chroma, qdrant, pinecone, weaviate, custom
      collection: "economist_kb"
      top_k: 5
      similarity_threshold: 0.7
      # Provider-specific config (optional)
      config:
        host: "${VECTOR_DB_HOST}"
        port: "${VECTOR_DB_PORT}"
        api_key: "${VECTOR_DB_API_KEY}"
    
    # Document storage configuration
    documents:
      type: "local"  # local, s3, azure, gcs, custom
      paths:
        - "knowledge/economics/market-analysis.md"
        - "knowledge/economics/policy-impacts.md"
      # Provider-specific config (optional)
      config:
        bucket: "${FILE_STORAGE_BUCKET}"
        endpoint: "${FILE_STORAGE_ENDPOINT}"
        access_key: "${FILE_STORAGE_ACCESS_KEY}"
        secret_key: "${FILE_STORAGE_SECRET_KEY}"
  
  # Behavior settings
  behavior:
    temperature: 0.3
    max_tokens: 2000
    response_style: "analytical"
    tone: "professional"
  
  # Capabilities
  capabilities:
    - "market_analysis"
    - "policy_impact"
    - "unit_economics"
    - "risk_assessment"
  
  # Constraints
  constraints:
    - "Always cite data sources when available"
    - "Provide quantitative analysis when possible"
  
  # Metadata
  metadata:
    category: "analyst"
    tags: ["economics", "finance", "analysis"]
    usage_limits:
      max_requests_per_hour: 100
```

## User Custom Policies

Users can provide their own policies via:

1. **Volume mount** (Docker):
   ```yaml
   volumes:
     - ./user-policies:/app/agents/policies/user
   ```

2. **Environment variable**:
   ```bash
   AGENT_POLICIES_PATH=/app/agents/policies/user
   ```

3. **API endpoint** (future):
   - Upload policies via API
   - Hot reload without restart

## Vector DB Integration

### Supported Providers

1. **Chroma** (default, embedded)
   ```yaml
   vector_db:
     type: "chroma"
     collection: "agent_kb"
   ```

2. **Qdrant** (self-hosted)
   ```yaml
   vector_db:
     type: "qdrant"
     collection: "agent_kb"
     config:
       host: "localhost"
       port: 6333
   ```

3. **Pinecone** (cloud)
   ```yaml
   vector_db:
     type: "pinecone"
     collection: "agent-kb"
     config:
       api_key: "${PINECONE_API_KEY}"
       environment: "us-east-1"
   ```

4. **Weaviate** (enterprise)
   ```yaml
   vector_db:
     type: "weaviate"
     collection: "AgentKB"
     config:
       url: "http://localhost:8080"
       api_key: "${WEAVIATE_API_KEY}"
   ```

5. **Custom** (plugin)
   ```yaml
   vector_db:
     type: "custom"
     provider: "my_custom_provider"
     config:
       # Custom configuration
   ```

## File Storage Integration

### Supported Providers

1. **Local** (default)
   ```yaml
   documents:
     type: "local"
     paths:
       - "/app/knowledge/agent-docs"
   ```

2. **S3-compatible**
   ```yaml
   documents:
     type: "s3"
     paths:
       - "s3://bucket/agent-docs/"
     config:
       endpoint: "https://s3.amazonaws.com"
       bucket: "agent-documents"
       access_key: "${S3_ACCESS_KEY}"
       secret_key: "${S3_SECRET_KEY}"
   ```

3. **Azure Blob Storage**
   ```yaml
   documents:
     type: "azure"
     paths:
       - "azure://container/agent-docs/"
     config:
       account_name: "${AZURE_ACCOUNT_NAME}"
       account_key: "${AZURE_ACCOUNT_KEY}"
   ```

4. **Google Cloud Storage**
   ```yaml
   documents:
     type: "gcs"
     paths:
       - "gs://bucket/agent-docs/"
     config:
       project_id: "${GCS_PROJECT_ID}"
       credentials: "${GCS_CREDENTIALS_JSON}"
   ```

5. **Custom** (plugin)
   ```yaml
   documents:
     type: "custom"
     provider: "my_custom_storage"
     config:
       # Custom configuration
   ```

## Plugin System

Users can provide custom vector DB and file storage implementations:

```python
# app/knowledge_base/plugins/vector_db.py
from abc import ABC, abstractmethod

class VectorDBProvider(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int) -> list[dict]:
        pass
    
    @abstractmethod
    def add_documents(self, documents: list[dict]):
        pass

# User's custom implementation
class MyCustomVectorDB(VectorDBProvider):
    def search(self, query: str, top_k: int) -> list[dict]:
        # Custom implementation
        pass
```

Register via environment:
```bash
VECTOR_DB_PLUGIN_PATH=/app/plugins
```

## Docker Integration

Users can integrate their own services via Docker Compose:

```yaml
services:
  ai-service:
    image: woragis/ai-service:latest
    volumes:
      - ./user-policies:/app/agents/policies/user
      - ./knowledge:/app/knowledge
    environment:
      - VECTOR_DB_TYPE=qdrant
      - VECTOR_DB_HOST=qdrant
      - VECTOR_DB_PORT=6333
      - FILE_STORAGE_TYPE=s3
      - FILE_STORAGE_BUCKET=my-bucket
    depends_on:
      - qdrant
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
```

## Implementation Plan

1. **YAML Parser** - Load and validate policies
2. **Vector DB Abstraction** - Interface for multiple providers
3. **File Storage Abstraction** - Interface for multiple providers
4. **Plugin System** - Allow custom implementations
5. **Hot Reload** - Update policies without restart
6. **Validation** - Schema validation for YAML

## Benefits

✅ **Flexibility** - Users choose their infrastructure
✅ **Portability** - Works with any vector DB/storage
✅ **Extensibility** - Plugin system for custom needs
✅ **No Lock-in** - Can switch providers easily
✅ **Docker-friendly** - Works with Docker Compose


