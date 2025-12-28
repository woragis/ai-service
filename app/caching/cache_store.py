"""
In-memory cache store implementation.

Provides LRU, LFU, and FIFO eviction policies.
"""

import time
import hashlib
from typing import Optional, Dict, Any, Tuple
from collections import OrderedDict
from threading import Lock
from app.logger import get_logger
from app.caching.policy import get_caching_policy_loader

logger = get_logger()


class CacheEntry:
    """A single cache entry."""
    
    def __init__(self, key: str, value: Any, ttl_seconds: int):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at
        self.size_bytes = self._estimate_size(value)
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate size of cached value in bytes."""
        if isinstance(value, str):
            return len(value.encode('utf-8'))
        elif isinstance(value, (dict, list)):
            return len(str(value).encode('utf-8'))
        else:
            return len(str(value).encode('utf-8'))
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.expires_at
    
    def access(self):
        """Record access to this entry."""
        self.access_count += 1
        self.last_accessed = time.time()


class LRUCache:
    """Least Recently Used cache implementation."""
    
    def __init__(self, max_entries: int, max_size_mb: int):
        self.max_entries = max_entries
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._current_size_bytes = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.access()
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int):
        """Set value in cache."""
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Check if we need to evict
            entry = CacheEntry(key, value, ttl_seconds)
            
            # Evict until we have space
            while (len(self._cache) >= self.max_entries or 
                   self._current_size_bytes + entry.size_bytes > self.max_size_bytes):
                if not self._evict_one():
                    break  # Can't evict more
            
            # Add new entry
            self._cache[key] = entry
            self._current_size_bytes += entry.size_bytes
    
    def _remove_entry(self, key: str):
        """Remove an entry from cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size_bytes -= entry.size_bytes
    
    def _evict_one(self) -> bool:
        """Evict least recently used entry."""
        if not self._cache:
            return False
        
        # Remove first (oldest) entry
        key, entry = self._cache.popitem(last=False)
        self._current_size_bytes -= entry.size_bytes
        logger.debug("Evicted cache entry", key=key, reason="lru")
        return True
    
    def clear_expired(self):
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                self._remove_entry(key)
            if expired_keys:
                logger.debug("Cleared expired cache entries", count=len(expired_keys))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self.clear_expired()
            return {
                "entries": len(self._cache),
                "max_entries": self.max_entries,
                "size_bytes": self._current_size_bytes,
                "max_size_bytes": self.max_size_bytes,
                "size_mb": self._current_size_bytes / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
            }


class LFUCache:
    """Least Frequently Used cache implementation."""
    
    def __init__(self, max_entries: int, max_size_mb: int):
        self.max_entries = max_entries
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._current_size_bytes = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            entry.access()
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int):
        """Set value in cache."""
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Check if we need to evict
            entry = CacheEntry(key, value, ttl_seconds)
            
            # Evict until we have space
            while (len(self._cache) >= self.max_entries or 
                   self._current_size_bytes + entry.size_bytes > self.max_size_bytes):
                if not self._evict_one():
                    break  # Can't evict more
            
            # Add new entry
            self._cache[key] = entry
            self._current_size_bytes += entry.size_bytes
    
    def _remove_entry(self, key: str):
        """Remove an entry from cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size_bytes -= entry.size_bytes
    
    def _evict_one(self) -> bool:
        """Evict least frequently used entry."""
        if not self._cache:
            return False
        
        # Find entry with lowest access count
        min_access_count = min(entry.access_count for entry in self._cache.values())
        candidates = [
            (key, entry) for key, entry in self._cache.items()
            if entry.access_count == min_access_count
        ]
        
        # If tie, use oldest
        key, entry = min(candidates, key=lambda x: x[1].created_at)
        self._remove_entry(key)
        logger.debug("Evicted cache entry", key=key, reason="lfu", access_count=entry.access_count)
        return True
    
    def clear_expired(self):
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                self._remove_entry(key)
            if expired_keys:
                logger.debug("Cleared expired cache entries", count=len(expired_keys))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self.clear_expired()
            return {
                "entries": len(self._cache),
                "max_entries": self.max_entries,
                "size_bytes": self._current_size_bytes,
                "max_size_bytes": self.max_size_bytes,
                "size_mb": self._current_size_bytes / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
            }


class FIFOCache:
    """First In First Out cache implementation."""
    
    def __init__(self, max_entries: int, max_size_mb: int):
        self.max_entries = max_entries
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._current_size_bytes = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            entry.access()
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int):
        """Set value in cache."""
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Check if we need to evict
            entry = CacheEntry(key, value, ttl_seconds)
            
            # Evict until we have space
            while (len(self._cache) >= self.max_entries or 
                   self._current_size_bytes + entry.size_bytes > self.max_size_bytes):
                if not self._evict_one():
                    break  # Can't evict more
            
            # Add new entry at end
            self._cache[key] = entry
            self._current_size_bytes += entry.size_bytes
    
    def _remove_entry(self, key: str):
        """Remove an entry from cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size_bytes -= entry.size_bytes
    
    def _evict_one(self) -> bool:
        """Evict oldest entry."""
        if not self._cache:
            return False
        
        # Remove first (oldest) entry
        key, entry = self._cache.popitem(last=False)
        self._current_size_bytes -= entry.size_bytes
        logger.debug("Evicted cache entry", key=key, reason="fifo")
        return True
    
    def clear_expired(self):
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                self._remove_entry(key)
            if expired_keys:
                logger.debug("Cleared expired cache entries", count=len(expired_keys))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self.clear_expired()
            return {
                "entries": len(self._cache),
                "max_entries": self.max_entries,
                "size_bytes": self._current_size_bytes,
                "max_size_bytes": self.max_size_bytes,
                "size_mb": self._current_size_bytes / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
            }


def create_cache_store(eviction_policy: str, max_entries: int, max_size_mb: int):
    """Create a cache store with the specified eviction policy."""
    if eviction_policy == "lru":
        return LRUCache(max_entries, max_size_mb)
    elif eviction_policy == "lfu":
        return LFUCache(max_entries, max_size_mb)
    elif eviction_policy == "fifo":
        return FIFOCache(max_entries, max_size_mb)
    else:
        logger.warn("Unknown eviction policy, using LRU", policy=eviction_policy)
        return LRUCache(max_entries, max_size_mb)

