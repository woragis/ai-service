"""
Semantic similarity caching.

Caches responses based on semantic similarity of queries.
"""

import hashlib
from typing import Optional, Dict, Any, Tuple, List
from threading import Lock
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # Optional dependency
from app.logger import get_logger
from app.caching.policy import get_caching_policy_loader
from app.caching.cache_store import CacheEntry

logger = get_logger()


class SemanticCache:
    """Semantic similarity-based cache."""
    
    def __init__(self):
        self.logger = get_logger()
        self._lock = Lock()
        self._embedding_model: Optional[SentenceTransformer] = None
        self._query_embeddings: Dict[str, np.ndarray] = {}  # cache_key -> embedding
        self._cache_entries: Dict[str, CacheEntry] = {}  # cache_key -> entry
        self._max_entries = 10000
        self._similarity_threshold = 0.85
        self._load_config()
    
    def _load_config(self):
        """Load configuration from policy."""
        policy = get_caching_policy_loader().get_policy()
        if policy.semantic_similarity.enabled:
            try:
                self._embedding_model = SentenceTransformer(
                    policy.semantic_similarity.embedding_model
                )
                self._similarity_threshold = policy.semantic_similarity.similarity_threshold
                self._max_entries = policy.semantic_similarity.max_cache_entries
                self.logger.info("Semantic cache initialized", 
                               model=policy.semantic_similarity.embedding_model,
                               threshold=self._similarity_threshold)
            except Exception as e:
                self.logger.error("Failed to load embedding model", error=str(e))
                self._embedding_model = None
    
    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text."""
        if not self._embedding_model:
            return None
        
        try:
            return self._embedding_model.encode(text, normalize_embeddings=True)
        except Exception as e:
            self.logger.error("Failed to generate embedding", error=str(e))
            return None
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return float(np.dot(vec1, vec2))
    
    def find_similar(self, query: str, agent_name: str = "") -> Optional[Tuple[str, Any]]:
        """
        Find a similar cached query and return its response.
        
        Args:
            query: The query text
            agent_name: Agent name (for scoping)
        
        Returns:
            Tuple of (cache_key, cached_value) if similar query found, None otherwise
        """
        policy = get_caching_policy_loader().get_policy()
        if not policy.semantic_similarity.enabled or not self._embedding_model:
            return None
        
        with self._lock:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query)
            if query_embedding is None:
                return None
            
            # Search for similar queries
            best_similarity = 0.0
            best_key = None
            
            for cache_key, cached_embedding in self._query_embeddings.items():
                # Check if entry is expired
                if cache_key in self._cache_entries:
                    entry = self._cache_entries[cache_key]
                    if entry.is_expired():
                        continue
                else:
                    continue
                
                # Calculate similarity
                similarity = self._cosine_similarity(query_embedding, cached_embedding)
                
                if similarity > best_similarity and similarity >= self._similarity_threshold:
                    best_similarity = similarity
                    best_key = cache_key
            
            if best_key:
                entry = self._cache_entries[best_key]
                entry.access()
                self.logger.debug("Found similar cached query", 
                               cache_key=best_key, 
                               similarity=best_similarity)
                return (best_key, entry.value)
            
            return None
    
    def store(self, cache_key: str, query: str, value: Any, ttl_seconds: int):
        """
        Store a query and response in semantic cache.
        
        Args:
            cache_key: Unique cache key
            query: The query text
            value: The response value to cache
            ttl_seconds: TTL in seconds
        """
        policy = get_caching_policy_loader().get_policy()
        if not policy.semantic_similarity.enabled or not self._embedding_model:
            return
        
        with self._lock:
            # Generate and store embedding
            query_embedding = self._generate_embedding(query)
            if query_embedding is None:
                return
            
            # Create cache entry
            entry = CacheEntry(cache_key, value, ttl_seconds)
            
            # Evict if needed
            while len(self._query_embeddings) >= self._max_entries:
                # Remove oldest entry
                if self._query_embeddings:
                    oldest_key = min(
                        self._query_embeddings.keys(),
                        key=lambda k: self._cache_entries.get(k, CacheEntry(k, None, 0)).created_at
                    )
                    self._query_embeddings.pop(oldest_key, None)
                    self._cache_entries.pop(oldest_key, None)
            
            # Store
            self._query_embeddings[cache_key] = query_embedding
            self._cache_entries[cache_key] = entry
            
            self.logger.debug("Stored query in semantic cache", cache_key=cache_key)
    
    def clear_expired(self):
        """Remove expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache_entries.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                self._query_embeddings.pop(key, None)
                self._cache_entries.pop(key, None)
            if expired_keys:
                self.logger.debug("Cleared expired semantic cache entries", count=len(expired_keys))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get semantic cache statistics."""
        with self._lock:
            self.clear_expired()
            return {
                "entries": len(self._query_embeddings),
                "max_entries": self._max_entries,
                "similarity_threshold": self._similarity_threshold,
                "enabled": self._embedding_model is not None,
            }


# Global semantic cache instance
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> Optional[SemanticCache]:
    """Get the global semantic cache instance."""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache

