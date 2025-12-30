"""
Feature flag policy definitions and loader.

Defines feature toggles for RAG, streaming, providers, and other features.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


@dataclass
class RAGConfig:
    """RAG (Retrieval-Augmented Generation) configuration."""
    enabled: bool = True
    per_agent_enabled: Dict[str, bool] = field(default_factory=dict)  # agent_name -> enabled
    default_enabled: bool = True  # Default for agents not in per_agent_enabled


@dataclass
class StreamingConfig:
    """Streaming configuration."""
    enabled: bool = True
    per_endpoint_enabled: Dict[str, bool] = field(default_factory=dict)  # endpoint -> enabled


@dataclass
class ProviderConfig:
    """Provider enable/disable configuration."""
    enabled_providers: List[str] = field(default_factory=lambda: ["openai", "anthropic", "cipher", "xai"])
    disabled_providers: List[str] = field(default_factory=list)


@dataclass
class FeatureFlags:
    """Feature flags configuration."""
    version: str = "1.0.0"
    rag: RAGConfig = field(default_factory=RAGConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    providers: ProviderConfig = field(default_factory=ProviderConfig)
    custom_flags: Dict[str, bool] = field(default_factory=dict)  # Custom feature flags


@dataclass
class FeaturePolicy:
    """Feature flag policy configuration."""
    version: str = "1.0.0"
    features: FeatureFlags = field(default_factory=FeatureFlags)


class FeaturePolicyLoader:
    """Loads and manages feature flag policies from YAML files."""
    
    def __init__(self, policies_path: str = "/app/policies")
        self.policies_path = Path(policies_path)
        self.logger = get_logger()
        self._policy: Optional[FeaturePolicy] = None
        self._load_policy()
    
    def _load_policy(self):
        """Load policy from YAML file."""
        policy_file = self.policies_path / "features.yaml"
        
        if not policy_file.exists():
            self.logger.warn("Feature policy file not found, using defaults", path=str(policy_file))
            self._policy = FeaturePolicy()
            return
        
        try:
            with open(policy_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "features" not in data:
                raise ValueError("Invalid feature policy structure: missing 'features' key")
            
            features_data = data["features"]
            
            policy = FeaturePolicy(
                version=data.get("version", "1.0.0"),
                features=FeatureFlags(
                    version=features_data.get("version", "1.0.0"),
                    rag=RAGConfig(**features_data.get("rag", {})),
                    streaming=StreamingConfig(**features_data.get("streaming", {})),
                    providers=ProviderConfig(**features_data.get("providers", {})),
                    custom_flags=features_data.get("custom_flags", {}),
                ),
            )
            
            self._policy = policy
            self.logger.info("Feature policy loaded", file=str(policy_file))
        except Exception as e:
            self.logger.error("Failed to load feature policy", error=str(e), file=str(policy_file))
            self._policy = FeaturePolicy()  # Fallback to defaults
            self.logger.info("Default feature policy loaded due to error")
    
    def get_policy(self) -> FeaturePolicy:
        """Get the current policy."""
        if self._policy is None:
            self._load_policy()
        return self._policy if self._policy else FeaturePolicy()
    
    def reload(self):
        """Reload policy from file (hot reload)."""
        self._policy = None
        self._load_policy()
        self.logger.info("Feature policies reloaded")


_policy_loader: Optional[FeaturePolicyLoader] = None


def get_feature_policy_loader() -> FeaturePolicyLoader:
    """Get the global feature policy loader instance."""
    global _policy_loader
    if _policy_loader is None:
        policies_path = os.getenv("FEATURE_POLICIES_PATH", "/app/policies")
        _policy_loader = FeaturePolicyLoader(policies_path=policies_path)
    return _policy_loader

