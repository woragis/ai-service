"""
Cost control policy definitions and loader.

Defines budget limits, token usage limits, and cost-based routing policies.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


@dataclass
class BudgetLimit:
    """Budget limit configuration."""
    enabled: bool = True
    daily_limit_usd: float = 100.0
    monthly_limit_usd: float = 3000.0
    per_request_limit_usd: float = 1.0
    reset_hour: int = 0  # Hour of day to reset daily budget (0-23)


@dataclass
class TokenLimit:
    """Token usage limits per request."""
    enabled: bool = True
    max_input_tokens: int = 100000  # ~75k words
    max_output_tokens: int = 4000
    max_total_tokens: int = 104000


@dataclass
class CostRoutingConfig:
    """Cost-based routing configuration."""
    enabled: bool = True
    prefer_cheaper_models: bool = True
    cost_threshold_usd: float = 0.01  # Use cheaper models if estimated cost > threshold
    quality_threshold: float = 0.7  # Minimum quality score when using cost-based routing


@dataclass
class CostControlPolicy:
    """Cost control policy configuration."""
    version: str = "1.0.0"
    budget: BudgetLimit = field(default_factory=BudgetLimit)
    token_limits: TokenLimit = field(default_factory=TokenLimit)
    cost_routing: CostRoutingConfig = field(default_factory=CostRoutingConfig)


class CostControlPolicyLoader:
    """Loads and manages cost control policies from YAML files."""
    
    def __init__(self, policies_path: str = "/app/policies")
        self.policies_path = Path(policies_path)
        self.logger = get_logger()
        self._policy: Optional[CostControlPolicy] = None
        self._load_policy()
    
    def _load_policy(self):
        """Load policy from YAML file."""
        policy_file = self.policies_path / "cost_control.yaml"
        
        if not policy_file.exists():
            self.logger.warn("Cost control policy file not found, using defaults", path=str(policy_file))
            self._policy = CostControlPolicy()
            return
        
        try:
            with open(policy_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "cost_control" not in data:
                raise ValueError("Invalid cost control policy structure: missing 'cost_control' key")
            
            cost_control_data = data["cost_control"]
            
            policy = CostControlPolicy(
                version=data.get("version", "1.0.0"),
                budget=BudgetLimit(**cost_control_data.get("budget", {})),
                token_limits=TokenLimit(**cost_control_data.get("token_limits", {})),
                cost_routing=CostRoutingConfig(**cost_control_data.get("cost_routing", {})),
            )
            
            self._policy = policy
            self.logger.info("Cost control policy loaded", file=str(policy_file))
        except Exception as e:
            self.logger.error("Failed to load cost control policy", error=str(e), file=str(policy_file))
            self._policy = CostControlPolicy()  # Fallback to defaults
            self.logger.info("Default cost control policy loaded due to error")
    
    def get_policy(self) -> CostControlPolicy:
        """Get the current policy."""
        if self._policy is None:
            self._load_policy()
        return self._policy if self._policy else CostControlPolicy()
    
    def reload(self):
        """Reload policy from file (hot reload)."""
        self._policy = None
        self._load_policy()
        self.logger.info("Cost control policies reloaded")


_policy_loader: Optional[CostControlPolicyLoader] = None


def get_cost_control_policy_loader() -> CostControlPolicyLoader:
    """Get the global cost control policy loader instance."""
    global _policy_loader
    if _policy_loader is None:
        policies_path = os.getenv("COST_CONTROL_POLICIES_PATH", "/app/policies")
        _policy_loader = CostControlPolicyLoader(policies_path=policies_path)
    return _policy_loader

