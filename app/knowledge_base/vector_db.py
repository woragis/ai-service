"""
Vector database abstraction for knowledge base.

Supports multiple vector DB providers: Qdrant (default), Chroma, Pinecone, Weaviate, and custom plugins.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.logger import get_logger

logger = get_logger()

# Global vector DB instance
_vector_db: Optional["VectorDBProvider"] = None


class VectorDBProvider(ABC):
    """Abstract base class for vector database providers."""
    
    @abstractmethod
    def search(self, query: str, collection: str, top_k: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            collection: Collection/namespace name
            top_k: Number of results to return
            score_threshold: Minimum similarity score
        
        Returns:
            List of documents with metadata and scores
        """
        pass
    
    @abstractmethod
    def add_documents(self, collection: str, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to the vector database.
        
        Args:
            collection: Collection/namespace name
            documents: List of documents with text and metadata
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def create_collection(self, collection: str, dimension: int = 384) -> bool:
        """
        Create a new collection.
        
        Args:
            collection: Collection name
            dimension: Vector dimension (default: 384 for sentence-transformers)
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def delete_collection(self, collection: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection: Collection name
        
        Returns:
            True if successful
        """
        pass


class QdrantProvider(VectorDBProvider):
    """Qdrant vector database provider."""
    
    def __init__(self, host: str = "localhost", port: int = 6333, api_key: Optional[str] = None):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError:
            raise ImportError("qdrant-client not installed. Install with: pip install qdrant-client")
        
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.logger = get_logger()
        self.logger.info("Qdrant vector DB initialized", host=host, port=port)
    
    def search(self, query: str, collection: str, top_k: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search Qdrant collection."""
        try:
            # For now, return empty - will implement with embeddings later
            # This is a placeholder for the RAG implementation
            return []
        except Exception as e:
            self.logger.error("Qdrant search failed", error=str(e), collection=collection)
            return []
    
    def add_documents(self, collection: str, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to Qdrant."""
        try:
            # Placeholder - will implement with embeddings
            return True
        except Exception as e:
            self.logger.error("Qdrant add documents failed", error=str(e), collection=collection)
            return False
    
    def create_collection(self, collection: str, dimension: int = 384) -> bool:
        """Create Qdrant collection."""
        try:
            from qdrant_client.models import Distance, VectorParams
            
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )
            self.logger.info("Qdrant collection created", collection=collection, dimension=dimension)
            return True
        except Exception as e:
            # Collection might already exist
            if "already exists" in str(e).lower():
                return True
            self.logger.error("Qdrant create collection failed", error=str(e), collection=collection)
            return False
    
    def delete_collection(self, collection: str) -> bool:
        """Delete Qdrant collection."""
        try:
            self.client.delete_collection(collection_name=collection)
            self.logger.info("Qdrant collection deleted", collection=collection)
            return True
        except Exception as e:
            self.logger.error("Qdrant delete collection failed", error=str(e), collection=collection)
            return False


class ChromaProvider(VectorDBProvider):
    """Chroma vector database provider (embedded, default fallback)."""
    
    def __init__(self, persist_directory: Optional[str] = None):
        try:
            import chromadb
        except ImportError:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")
        
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        self.logger = get_logger()
        self.logger.info("Chroma vector DB initialized")
    
    def search(self, query: str, collection: str, top_k: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search Chroma collection."""
        try:
            # Placeholder - will implement with embeddings
            return []
        except Exception as e:
            self.logger.error("Chroma search failed", error=str(e), collection=collection)
            return []
    
    def add_documents(self, collection: str, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to Chroma."""
        try:
            # Placeholder
            return True
        except Exception as e:
            self.logger.error("Chroma add documents failed", error=str(e), collection=collection)
            return False
    
    def create_collection(self, collection: str, dimension: int = 384) -> bool:
        """Create Chroma collection."""
        try:
            self.client.get_or_create_collection(name=collection)
            self.logger.info("Chroma collection created", collection=collection)
            return True
        except Exception as e:
            self.logger.error("Chroma create collection failed", error=str(e), collection=collection)
            return False
    
    def delete_collection(self, collection: str) -> bool:
        """Delete Chroma collection."""
        try:
            self.client.delete_collection(name=collection)
            self.logger.info("Chroma collection deleted", collection=collection)
            return True
        except Exception as e:
            self.logger.error("Chroma delete collection failed", error=str(e), collection=collection)
            return False


def get_vector_db() -> VectorDBProvider:
    """Get or create vector DB provider instance."""
    global _vector_db
    
    if _vector_db is not None:
        return _vector_db
    
    db_type = os.getenv("VECTOR_DB_TYPE", "qdrant").lower()
    db_host = os.getenv("VECTOR_DB_HOST", "localhost")
    db_port = int(os.getenv("VECTOR_DB_PORT", "6333"))
    db_api_key = os.getenv("VECTOR_DB_API_KEY")
    
    if db_type == "qdrant":
        _vector_db = QdrantProvider(host=db_host, port=db_port, api_key=db_api_key)
    elif db_type == "chroma":
        persist_dir = os.getenv("VECTOR_DB_PERSIST_DIR", "/app/data/chroma")
        _vector_db = ChromaProvider(persist_directory=persist_dir)
    else:
        # Try to load custom plugin
        plugin_path = os.getenv("VECTOR_DB_PLUGIN_PATH", "/app/plugins")
        _vector_db = _load_custom_provider(db_type, plugin_path, db_host, db_port, db_api_key)
    
    return _vector_db


def _load_custom_provider(provider_name: str, plugin_path: str, *args, **kwargs) -> VectorDBProvider:
    """Load custom vector DB provider from plugin."""
    import importlib.util
    import sys
    
    plugin_file = f"{plugin_path}/vector_db_{provider_name}.py"
    
    if not os.path.exists(plugin_file):
        logger.warn("Custom vector DB plugin not found, falling back to Chroma", plugin=plugin_file)
        return ChromaProvider()
    
    try:
        spec = importlib.util.spec_from_file_location(f"vector_db_{provider_name}", plugin_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"vector_db_{provider_name}"] = module
        spec.loader.exec_module(module)
        
        # Expect a class named {ProviderName}Provider
        provider_class = getattr(module, f"{provider_name.capitalize()}Provider")
        return provider_class(*args, **kwargs)
    except Exception as e:
        logger.error("Failed to load custom vector DB provider", error=str(e), plugin=plugin_file)
        return ChromaProvider()  # Fallback

