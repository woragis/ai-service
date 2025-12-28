"""
Cache manager that orchestrates regular and semantic caching.
"""

import hashlib
import time
from typing import Optional, Any, Tuple
from app.logger import get_logger
from app.caching.policy import get_caching_policy_loader
from app.caching.cache_store import create_cache_store, CacheEntry
from app.caching.semantic_cache import get_semantic_cache

logger = get_logger()


class CacheManager:
    """Manages both regular and semantic caching."""
    
    def __init__(self):
        self.logger = get_logger()
        self._regular_cache = None
        self._semantic_cache = None
        self._load_caches()
    
    def _load_caches(self):
        """Initialize cache stores based on policy."""
        policy = get_caching_policy_loader().get_policy()
        
        if policy.enabled:
            # Create regular cache store
            self._regular_cache = create_cache_store(
                eviction_policy=policy.size_limits.eviction_policy,
                max_entries=policy.size_limits.max_entries,
                max_size_mb=policy.size_limits.max_size_mb,
            )
            self.logger.info("Regular cache initialized", 
                           policy=policy.size_limits.eviction_policy,
                           max_entries=policy.size_limits.max_entries)
        
        # Initialize semantic cache
        if policy.semantic_similarity.enabled:
            self._semantic_cache = get_semantic_cache()
    
    def _generate_cache_key(
        self, 
        query: str, 
        agent_name: str, 
        provider: str, 
        model: Optional[str],
        endpoint: str = "/v1/chat"
    ) -> str:
        """Generate a cache key for a request."""
        key_parts = [
            endpoint,
            agent_name,
            provider,
            model or "default",
            query,
        ]
        key_string = "|".join(str(part) for part in key_parts)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def _get_ttl(self, agent_name: str, endpoint: str) -> int:
        """Get TTL for a request based on agent and endpoint."""
        policy = get_caching_policy_loader().get_policy()
        ttl_config = policy.ttl
        
        # Check per-agent TTL
        if agent_name in ttl_config.per_agent_ttl:
            return ttl_config.per_agent_ttl[agent_name]
        
        # Check per-endpoint TTL
        if endpoint in ttl_config.per_endpoint_ttl:
            return ttl_config.per_endpoint_ttl[endpoint]
        
        # Use default
        return ttl_config.default_ttl_seconds
    
    def get(
        self,
        query: str,
        agent_name: str,
        provider: str,
        model: Optional[str],
        endpoint: str = "/v1/chat"
    ) -> Optional[Any]:
        """
        Get cached response for a request.
        
        Returns:
            Cached response if found, None otherwise
        """
        policy = get_caching_policy_loader().get_policy()
        if not policy.enabled:
            return None
        
        # Try regular cache first
        if self._regular_cache:
            cache_key = self._generate_cache_key(query, agent_name, provider, model, endpoint)
            cached_value = self._regular_cache.get(cache_key)
            if cached_value is not None:
                self.logger.debug("Cache hit (regular)", cache_key=cache_key[:16])
                return cached_value
        
        # Try semantic cache
        if self._semantic_cache:
            similar_result = self._semantic_cache.find_similar(query, agent_name)
            if similar_result:
                cache_key, cached_value = similar_result
                self.logger.debug("Cache hit (semantic)", cache_key=cache_key[:16])
                return cached_value
        
        return None
    
    def set(
        self,
        query: str,
        agent_name: str,
        provider: str,
        model: Optional[str],
        value: Any,
        endpoint: str = "/v1/chat"
    ):
        """
        Store a response in cache.
        
        Args:
            query: The query text
            agent_name: Agent name
            provider: Provider used
            model: Model used
            value: Response value to cache
            endpoint: Endpoint path
        """
        policy = get_caching_policy_loader().get_policy()
        if not policy.enabled:
            return
        
        ttl_seconds = self._get_ttl(agent_name, endpoint)
        cache_key = self._generate_cache_key(query, agent_name, provider, model, endpoint)
        
        # Store in regular cache
        if self._regular_cache:
            self._regular_cache.set(cache_key, value, ttl_seconds)
            self.logger.debug("Stored in regular cache", cache_key=cache_key[:16], ttl=ttl_seconds)
        
        # Store in semantic cache
        if self._semantic_cache:
            self._semantic_cache.store(cache_key, query, value, ttl_seconds)
            self.logger.debug("Stored in semantic cache", cache_key=cache_key[:16])
    
    def clear(self):
        """Clear all caches."""
        if self._regular_cache:
            # Clear regular cache by recreating it
            policy = get_caching_policy_loader().get_policy()
            self._regular_cache = create_cache_store(
                eviction_policy=policy.size_limits.eviction_policy,
                max_entries=policy.size_limits.max_entries,
                max_size_mb=policy.size_limits.max_size_mb,
            )
        
        if self._semantic_cache:
            # Clear semantic cache
            self._semantic_cache._query_embeddings.clear()
            self._semantic_cache._cache_entries.clear()
        
        self.logger.info("All caches cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        stats = {
            "enabled": get_caching_policy_loader().get_policy().enabled,
            "regular_cache": None,
            "semantic_cache": None,
        }
        
        if self._regular_cache:
            stats["regular_cache"] = self._regular_cache.get_stats()
        
        if self._semantic_cache:
            stats["semantic_cache"] = self._semantic_cache.get_stats()
        
        return stats


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def reset_cache_manager():
    """Reset the cache manager (for hot reload)."""
    global _cache_manager
    _cache_manager = CacheManager()

