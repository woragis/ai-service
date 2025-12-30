"""
Caching policy definitions and loader.

Defines cache TTL, size limits, and semantic similarity settings.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


@dataclass
class CacheTTLConfig:
    """Cache TTL configuration per agent/endpoint."""
    default_ttl_seconds: int = 3600  # 1 hour default
    per_agent_ttl: Dict[str, int] = field(default_factory=dict)  # agent_name -> ttl_seconds
    per_endpoint_ttl: Dict[str, int] = field(default_factory=dict)  # endpoint -> ttl_seconds


@dataclass
class SemanticSimilarityConfig:
    """Semantic similarity caching configuration."""
    enabled: bool = True
    similarity_threshold: float = 0.85  # 0-1, higher = more similar required
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # Lightweight model
    max_cache_entries: int = 10000  # Max number of cached queries for similarity search


@dataclass
class CacheSizeConfig:
    """Cache size limits configuration."""
    max_size_mb: int = 500  # Maximum cache size in MB
    max_entries: int = 10000  # Maximum number of cache entries
    eviction_policy: str = "lru"  # "lru", "lfu", "fifo"


@dataclass
class CachingPolicy:
    """Caching policy configuration."""
    version: str = "1.0.0"
    enabled: bool = True
    ttl: CacheTTLConfig = field(default_factory=CacheTTLConfig)
    semantic_similarity: SemanticSimilarityConfig = field(default_factory=SemanticSimilarityConfig)
    size_limits: CacheSizeConfig = field(default_factory=CacheSizeConfig)


class CachingPolicyLoader:
    """Loads and manages caching policies from YAML files."""
    
    def __init__(self, policies_path: str = "/app/policies"):
        self.policies_path = Path(policies_path)
        self.logger = get_logger()
        self._policy: Optional[CachingPolicy] = None
        self._load_policy()
    
    def _load_policy(self):
        """Load policy from YAML file."""
        policy_file = self.policies_path / "caching.yaml"
        
        if not policy_file.exists():
            self.logger.warn("Caching policy file not found, using defaults", path=str(policy_file))
            self._policy = CachingPolicy()
            return
        
        try:
            with open(policy_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "caching" not in data:
                raise ValueError("Invalid caching policy structure: missing 'caching' key")
            
            caching_data = data["caching"]
            
            ttl_data = caching_data.get("ttl", {})
            semantic_data = caching_data.get("semantic_similarity", {})
            size_data = caching_data.get("size_limits", {})
            
            policy = CachingPolicy(
                version=data.get("version", "1.0.0"),
                enabled=caching_data.get("enabled", True),
                ttl=CacheTTLConfig(
                    default_ttl_seconds=ttl_data.get("default_ttl_seconds", 3600),
                    per_agent_ttl=ttl_data.get("per_agent_ttl", {}),
                    per_endpoint_ttl=ttl_data.get("per_endpoint_ttl", {}),
                ),
                semantic_similarity=SemanticSimilarityConfig(
                    enabled=semantic_data.get("enabled", True),
                    similarity_threshold=semantic_data.get("similarity_threshold", 0.85),
                    embedding_model=semantic_data.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
                    max_cache_entries=semantic_data.get("max_cache_entries", 10000),
                ),
                size_limits=CacheSizeConfig(
                    max_size_mb=size_data.get("max_size_mb", 500),
                    max_entries=size_data.get("max_entries", 10000),
                    eviction_policy=size_data.get("eviction_policy", "lru"),
                ),
            )
            
            self._policy = policy
            self.logger.info("Caching policy loaded", file=str(policy_file))
        except Exception as e:
            self.logger.error("Failed to load caching policy", error=str(e), file=str(policy_file))
            self._policy = CachingPolicy()  # Fallback to defaults
            self.logger.info("Default caching policy loaded due to error")
    
    def get_policy(self) -> CachingPolicy:
        """Get the current policy."""
        if self._policy is None:
            self._load_policy()
        return self._policy if self._policy else CachingPolicy()
    
    def reload(self):
        """Reload policy from file (hot reload)."""
        self._policy = None
        self._load_policy()
        self.logger.info("Caching policies reloaded")


_policy_loader: Optional[CachingPolicyLoader] = None


def get_caching_policy_loader() -> CachingPolicyLoader:
    """Get the global caching policy loader instance."""
    global _policy_loader
    if _policy_loader is None:
        policies_path = os.getenv("CACHING_POLICIES_PATH", "/app/policies")
        _policy_loader = CachingPolicyLoader(policies_path=policies_path)
    return _policy_loader

