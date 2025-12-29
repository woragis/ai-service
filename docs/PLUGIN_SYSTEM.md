# Plugin System

## Overview

The AI service supports a plugin system that allows you to extend functionality with custom implementations for vector databases and file storage. This enables integration with proprietary systems or specialized storage solutions.

## Supported Plugin Types

### 1. Vector Database Plugins

Custom vector database implementations for RAG (Retrieval-Augmented Generation).

### 2. File Storage Plugins

Custom file storage implementations for knowledge base documents.

## Plugin Location

Plugins are loaded from the `/app/plugins` directory (or path specified by environment variable).

## Creating a Vector DB Plugin

### Plugin File Structure

Create a file: `plugins/vector_db_{provider_name}.py`

Example: `plugins/vector_db_custom.py`

### Implementation

```python
from app.knowledge_base.vector_db import VectorDBProvider
from typing import List, Dict, Any
from app.logger import get_logger

logger = get_logger()

class CustomProvider(VectorDBProvider):
    """Custom vector database provider."""
    
    def __init__(self, host: str, port: int, api_key: str = None):
        # Initialize your vector DB client
        self.host = host
        self.port = port
        self.api_key = api_key
        logger.info("Custom vector DB initialized", host=host, port=port)
    
    def search(self, query: str, collection: str, top_k: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Returns:
            List of documents with 'text' or 'content' key and optional metadata
        """
        # Implement your search logic
        results = []
        # ... your search implementation
        return results
    
    def add_documents(self, collection: str, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector database."""
        # Implement document addition
        return True
    
    def create_collection(self, collection: str, dimension: int = 384) -> bool:
        """Create a new collection."""
        # Implement collection creation
        return True
    
    def delete_collection(self, collection: str) -> bool:
        """Delete a collection."""
        # Implement collection deletion
        return True
```

### Naming Convention

- **File**: `vector_db_{provider_name}.py`
- **Class**: `{ProviderName}Provider` (e.g., `CustomProvider`)

### Configuration

```bash
VECTOR_DB_TYPE=custom
VECTOR_DB_HOST=your-host
VECTOR_DB_PORT=1234
VECTOR_DB_API_KEY=your-key
VECTOR_DB_PLUGIN_PATH=/app/plugins
```

## Creating a File Storage Plugin

### Plugin File Structure

Create a file: `plugins/file_storage_{provider_name}.py`

Example: `plugins/file_storage_custom.py`

### Implementation

```python
from app.knowledge_base.file_storage import FileStorageProvider
from typing import List, Optional
from app.logger import get_logger

logger = get_logger()

class CustomFileStorage(FileStorageProvider):
    """Custom file storage provider."""
    
    def __init__(self, base_path: str, **kwargs):
        # Initialize your storage client
        self.base_path = base_path
        logger.info("Custom file storage initialized", base_path=base_path)
    
    def read_file(self, path: str) -> Optional[str]:
        """Read file content."""
        # Implement file reading
        return None
    
    def list_files(self, path: str, pattern: str = "*.md") -> List[str]:
        """List files matching pattern."""
        # Implement file listing
        return []
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        # Implement existence check
        return False
```

### Naming Convention

- **File**: `file_storage_{provider_name}.py`
- **Class**: `{ProviderName}FileStorage` (e.g., `CustomFileStorage`)

### Configuration

```bash
FILE_STORAGE_TYPE=custom
FILE_STORAGE_BASE_PATH=/app/knowledge
FILE_STORAGE_PLUGIN_PATH=/app/plugins
```

## Plugin Loading

### Automatic Loading

Plugins are automatically loaded when:
1. The provider type doesn't match built-in providers
2. The plugin file exists in the plugin path
3. The plugin class follows naming conventions

### Fallback Behavior

If a plugin fails to load:
- **Vector DB**: Falls back to Chroma (embedded)
- **File Storage**: Falls back to LocalFileStorage

## Docker Integration

### Mount Plugin Directory

```yaml
volumes:
  - ./plugins:/app/plugins:ro
```

### Dockerfile

The Dockerfile already includes the plugins directory:

```dockerfile
COPY plugins /app/plugins
```

## Example: Pinecone Vector DB Plugin

```python
from app.knowledge_base.vector_db import VectorDBProvider
from typing import List, Dict, Any
import pinecone

class PineconeProvider(VectorDBProvider):
    def __init__(self, api_key: str, environment: str):
        pinecone.init(api_key=api_key, environment=environment)
        self.index = None
    
    def search(self, query: str, collection: str, top_k: int = 5, score_threshold: float = 0.7):
        if not self.index:
            self.index = pinecone.Index(collection)
        
        # Generate query embedding (using your embedding model)
        query_embedding = self._embed(query)
        
        # Search
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return [
            {"text": match.metadata.get("text", ""), "score": match.score}
            for match in results.matches
            if match.score >= score_threshold
        ]
    
    # ... implement other methods
```

## Example: Azure Blob Storage Plugin

```python
from app.knowledge_base.file_storage import FileStorageProvider
from azure.storage.blob import BlobServiceClient
from typing import List, Optional

class AzureFileStorage(FileStorageProvider):
    def __init__(self, connection_string: str, container_name: str):
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = container_name
    
    def read_file(self, path: str) -> Optional[str]:
        blob_client = self.client.get_blob_client(
            container=self.container,
            blob=path
        )
        return blob_client.download_blob().readall().decode("utf-8")
    
    # ... implement other methods
```

## Best Practices

1. **Error Handling** - Always handle errors gracefully
2. **Logging** - Use structured logging for debugging
3. **Type Hints** - Use proper type hints for IDE support
4. **Documentation** - Document your plugin's configuration
5. **Testing** - Test plugins independently before integration
6. **Fallback** - Handle missing dependencies gracefully

## Troubleshooting

### Plugin Not Loading

1. Check file naming: `vector_db_{name}.py` or `file_storage_{name}.py`
2. Check class naming: `{Name}Provider` or `{Name}FileStorage`
3. Verify plugin path: `VECTOR_DB_PLUGIN_PATH` or `FILE_STORAGE_PLUGIN_PATH`
4. Check logs for loading errors

### Plugin Errors

- Check logs for specific error messages
- Verify all dependencies are installed
- Test plugin independently
- Check environment variables

## Related Documentation

- [Vector DB Options](./VECTOR_DB_OPTIONS.md)
- [RAG Implementation](./VECTOR_DB_OPTIONS.md)
- [Agent Policies](./AGENT_POLICIES.md)

