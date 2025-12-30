"""
Routing policy loader and validator.

Loads routing policies from YAML files for model selection, fallback chains,
and cost/quality trade-offs.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


@dataclass
class ProviderConfig:
    """Configuration for a specific provider."""
    name: str
    priority: int = 0  # Lower = higher priority
    models: List[str] = field(default_factory=list)
    cost_tier: str = "medium"  # low, medium, high
    quality_tier: str = "medium"  # low, medium, high
    enabled: bool = True
    timeout: Optional[float] = None
    max_retries: int = 3


@dataclass
class FallbackChain:
    """Fallback chain configuration."""
    primary: str  # Provider name
    fallbacks: List[str] = field(default_factory=list)  # List of provider names
    conditions: Dict[str, Any] = field(default_factory=dict)  # Conditions for fallback


@dataclass
class QueryComplexityRule:
    """Rule for selecting provider based on query complexity."""
    complexity: str  # simple, medium, complex
    provider_preference: List[str] = field(default_factory=list)
    model_preference: Dict[str, str] = field(default_factory=dict)  # provider -> model
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostQualityTradeoff:
    """Cost vs quality trade-off configuration."""
    mode: str = "balanced"  # cost_optimized, balanced, quality_optimized
    cost_threshold: Optional[float] = None
    quality_threshold: Optional[float] = None
    provider_mapping: Dict[str, Dict[str, str]] = field(default_factory=dict)  # mode -> provider -> model


@dataclass
class RoutingPolicy:
    """Routing policy definition."""
    version: str = "1.0.0"
    name: str = "default"
    description: str = ""
    
    # Provider configurations
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    
    # Fallback chains
    fallback_chains: List[FallbackChain] = field(default_factory=list)
    
    # Query complexity rules
    complexity_rules: List[QueryComplexityRule] = field(default_factory=list)
    
    # Cost/quality trade-offs
    cost_quality: CostQualityTradeoff = field(default_factory=CostQualityTradeoff)
    
    # Default settings
    default_provider: str = "openai"
    default_model: Optional[str] = None
    enable_auto_routing: bool = True


class RoutingPolicyLoader:
    """Loads and validates routing policies from YAML files."""
    
    def __init__(self, policies_path: str = "/app/policies")
        self.policies_path = Path(policies_path)
        self.logger = get_logger()
        self._policy: Optional[RoutingPolicy] = None
        self._load_policy()
    
    def _load_policy(self):
        """Load routing policy from YAML file."""
        if not self.policies_path.exists():
            self.logger.warn("Routing policies directory not found, using defaults", path=str(self.policies_path))
            self._policy = self._create_default_policy()
            return
        
        # Look for routing.yaml or default.yaml
        policy_file = self.policies_path / "routing.yaml"
        if not policy_file.exists():
            policy_file = self.policies_path / "default.yaml"
        
        if not policy_file.exists():
            self.logger.info("No routing policy file found, using defaults")
            self._policy = self._create_default_policy()
            return
        
        try:
            with open(policy_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "routing" not in data:
                raise ValueError("Invalid routing policy structure: missing 'routing' key")
            
            routing_data = data["routing"]
            self._policy = self._load_routing_policy(routing_data)
            self.logger.info("Routing policy loaded", file=str(policy_file))
        except Exception as e:
            self.logger.error("Failed to load routing policy", error=str(e), file=str(policy_file))
            self._policy = self._create_default_policy()
    
    def _load_routing_policy(self, data: Dict[str, Any]) -> RoutingPolicy:
        """Load routing policy from data dictionary."""
        policy = RoutingPolicy(
            version=data.get("version", "1.0.0"),
            name=data.get("name", "default"),
            description=data.get("description", ""),
            default_provider=data.get("default_provider", "openai"),
            default_model=data.get("default_model"),
            enable_auto_routing=data.get("enable_auto_routing", True),
        )
        
        # Load providers
        if "providers" in data:
            for provider_name, provider_data in data["providers"].items():
                policy.providers[provider_name] = ProviderConfig(
                    name=provider_name,
                    priority=provider_data.get("priority", 0),
                    models=provider_data.get("models", []),
                    cost_tier=provider_data.get("cost_tier", "medium"),
                    quality_tier=provider_data.get("quality_tier", "medium"),
                    enabled=provider_data.get("enabled", True),
                    timeout=provider_data.get("timeout"),
                    max_retries=provider_data.get("max_retries", 3),
                )
        
        # Load fallback chains
        if "fallback_chains" in data:
            for chain_data in data["fallback_chains"]:
                policy.fallback_chains.append(FallbackChain(
                    primary=chain_data.get("primary", ""),
                    fallbacks=chain_data.get("fallbacks", []),
                    conditions=chain_data.get("conditions", {}),
                ))
        
        # Load complexity rules
        if "complexity_rules" in data:
            for rule_data in data["complexity_rules"]:
                policy.complexity_rules.append(QueryComplexityRule(
                    complexity=rule_data.get("complexity", "medium"),
                    provider_preference=rule_data.get("provider_preference", []),
                    model_preference=rule_data.get("model_preference", {}),
                    conditions=rule_data.get("conditions", {}),
                ))
        
        # Load cost/quality trade-offs
        if "cost_quality" in data:
            cq_data = data["cost_quality"]
            policy.cost_quality = CostQualityTradeoff(
                mode=cq_data.get("mode", "balanced"),
                cost_threshold=cq_data.get("cost_threshold"),
                quality_threshold=cq_data.get("quality_threshold"),
                provider_mapping=cq_data.get("provider_mapping", {}),
            )
        
        return policy
    
    def _create_default_policy(self) -> RoutingPolicy:
        """Create default routing policy."""
        policy = RoutingPolicy()
        
        # Default providers
        policy.providers["openai"] = ProviderConfig(
            name="openai",
            priority=1,
            models=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            cost_tier="medium",
            quality_tier="high",
        )
        policy.providers["anthropic"] = ProviderConfig(
            name="anthropic",
            priority=2,
            models=["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
            cost_tier="medium",
            quality_tier="high",
        )
        
        # Default fallback chain
        policy.fallback_chains.append(FallbackChain(
            primary="openai",
            fallbacks=["anthropic", "xai"],
        ))
        
        return policy
    
    def get_policy(self) -> RoutingPolicy:
        """Get current routing policy."""
        return self._policy or self._create_default_policy()
    
    def reload(self):
        """Reload routing policy (for hot reload)."""
        self._policy = None
        self._load_policy()
        self.logger.info("Routing policy reloaded")


# Global policy loader instance
_policy_loader: Optional[RoutingPolicyLoader] = None


def get_routing_policy_loader() -> RoutingPolicyLoader:
    """Get or create routing policy loader instance."""
    global _policy_loader
    
    if _policy_loader is None:
        policies_path = os.getenv("ROUTING_POLICIES_PATH", "/app/policies")
        _policy_loader = RoutingPolicyLoader(policies_path=policies_path)
    
    return _policy_loader

