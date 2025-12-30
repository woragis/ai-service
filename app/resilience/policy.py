"""
Resilience policy loader and validator.

Loads retry, circuit breaker, timeout, and graceful degradation policies from YAML.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


@dataclass
class RetryStrategy:
    """Retry strategy configuration."""
    max_attempts: int = 3
    backoff_type: str = "exponential"  # exponential, linear, fixed
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    multiplier: float = 2.0  # for exponential backoff
    retryable_errors: List[str] = field(default_factory=lambda: [
        "rate_limit", "timeout", "service_unavailable", "internal_server_error"
    ])


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes before half-open
    timeout: float = 60.0  # Seconds before attempting to close
    half_open_max_calls: int = 3  # Max calls in half-open state


@dataclass
class TimeoutConfig:
    """Timeout configuration."""
    default: float = 60.0  # Default timeout in seconds
    per_provider: Dict[str, float] = field(default_factory=dict)
    per_model: Dict[str, float] = field(default_factory=dict)
    per_endpoint: Dict[str, float] = field(default_factory=dict)


@dataclass
class GracefulDegradationRule:
    """Graceful degradation rule."""
    condition: str  # error_type, latency_threshold, etc.
    threshold: Any  # Threshold value
    action: str  # downgrade_model, use_fallback, return_cached, etc.
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    max_latency: Optional[float] = None  # ms


@dataclass
class ResiliencePolicy:
    """Resilience policy definition."""
    version: str = "1.0.0"
    name: str = "default"
    description: str = ""
    
    # Retry strategies per provider
    retry_strategies: Dict[str, RetryStrategy] = field(default_factory=dict)
    
    # Circuit breaker configs per provider
    circuit_breakers: Dict[str, CircuitBreakerConfig] = field(default_factory=dict)
    
    # Timeout configurations
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    
    # Graceful degradation rules
    degradation_rules: List[GracefulDegradationRule] = field(default_factory=list)
    
    # Global settings
    enable_circuit_breaker: bool = True
    enable_retry: bool = True
    enable_graceful_degradation: bool = True


class ResiliencePolicyLoader:
    """Loads and validates resilience policies from YAML files."""
    
    def __init__(self, policies_path: str = "/app/policies")
        self.policies_path = Path(policies_path)
        self.logger = get_logger()
        self._policy: Optional[ResiliencePolicy] = None
        self._load_policy()
    
    def _load_policy(self):
        """Load resilience policy from YAML file."""
        if not self.policies_path.exists():
            self.logger.warn("Resilience policies directory not found, using defaults", path=str(self.policies_path))
            self._policy = self._create_default_policy()
            return
        
        # Look for resilience.yaml or default.yaml
        policy_file = self.policies_path / "resilience.yaml"
        if not policy_file.exists():
            policy_file = self.policies_path / "default.yaml"
        
        if not policy_file.exists():
            self.logger.info("No resilience policy file found, using defaults")
            self._policy = self._create_default_policy()
            return
        
        try:
            with open(policy_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "resilience" not in data:
                raise ValueError("Invalid resilience policy structure: missing 'resilience' key")
            
            resilience_data = data["resilience"]
            self._policy = self._load_resilience_policy(resilience_data)
            self.logger.info("Resilience policy loaded", file=str(policy_file))
        except Exception as e:
            self.logger.error("Failed to load resilience policy", error=str(e), file=str(policy_file))
            self._policy = self._create_default_policy()
    
    def _load_resilience_policy(self, data: Dict[str, Any]) -> ResiliencePolicy:
        """Load resilience policy from data dictionary."""
        policy = ResiliencePolicy(
            version=data.get("version", "1.0.0"),
            name=data.get("name", "default"),
            description=data.get("description", ""),
            enable_circuit_breaker=data.get("enable_circuit_breaker", True),
            enable_retry=data.get("enable_retry", True),
            enable_graceful_degradation=data.get("enable_graceful_degradation", True),
        )
        
        # Load retry strategies
        if "retry_strategies" in data:
            for provider_name, strategy_data in data["retry_strategies"].items():
                policy.retry_strategies[provider_name] = RetryStrategy(
                    max_attempts=strategy_data.get("max_attempts", 3),
                    backoff_type=strategy_data.get("backoff_type", "exponential"),
                    initial_delay=strategy_data.get("initial_delay", 1.0),
                    max_delay=strategy_data.get("max_delay", 60.0),
                    multiplier=strategy_data.get("multiplier", 2.0),
                    retryable_errors=strategy_data.get("retryable_errors", [
                        "rate_limit", "timeout", "service_unavailable", "internal_server_error"
                    ]),
                )
        
        # Load circuit breaker configs
        if "circuit_breakers" in data:
            for provider_name, cb_data in data["circuit_breakers"].items():
                policy.circuit_breakers[provider_name] = CircuitBreakerConfig(
                    failure_threshold=cb_data.get("failure_threshold", 5),
                    success_threshold=cb_data.get("success_threshold", 2),
                    timeout=cb_data.get("timeout", 60.0),
                    half_open_max_calls=cb_data.get("half_open_max_calls", 3),
                )
        
        # Load timeout configs
        if "timeouts" in data:
            timeout_data = data["timeouts"]
            policy.timeouts = TimeoutConfig(
                default=timeout_data.get("default", 60.0),
                per_provider=timeout_data.get("per_provider", {}),
                per_model=timeout_data.get("per_model", {}),
                per_endpoint=timeout_data.get("per_endpoint", {}),
            )
        
        # Load graceful degradation rules
        if "graceful_degradation" in data:
            for rule_data in data["graceful_degradation"]:
                policy.degradation_rules.append(GracefulDegradationRule(
                    condition=rule_data.get("condition", ""),
                    threshold=rule_data.get("threshold"),
                    action=rule_data.get("action", "use_fallback"),
                    fallback_provider=rule_data.get("fallback_provider"),
                    fallback_model=rule_data.get("fallback_model"),
                    max_latency=rule_data.get("max_latency"),
                ))
        
        return policy
    
    def _create_default_policy(self) -> ResiliencePolicy:
        """Create default resilience policy."""
        policy = ResiliencePolicy()
        
        # Default retry strategies
        default_retry = RetryStrategy()
        policy.retry_strategies["openai"] = default_retry
        policy.retry_strategies["anthropic"] = default_retry
        policy.retry_strategies["xai"] = default_retry
        policy.retry_strategies["manus"] = default_retry
        
        # Default circuit breakers
        default_cb = CircuitBreakerConfig()
        policy.circuit_breakers["openai"] = default_cb
        policy.circuit_breakers["anthropic"] = default_cb
        
        # Default timeouts
        policy.timeouts = TimeoutConfig(
            default=60.0,
            per_provider={
                "openai": 60.0,
                "anthropic": 60.0,
                "xai": 60.0,
                "manus": 60.0,
            },
        )
        
        return policy
    
    def get_policy(self) -> ResiliencePolicy:
        """Get current resilience policy."""
        return self._policy or self._create_default_policy()
    
    def reload(self):
        """Reload resilience policy (for hot reload)."""
        self._policy = None
        self._load_policy()
        self.logger.info("Resilience policy reloaded")


# Global policy loader instance
_policy_loader: Optional[ResiliencePolicyLoader] = None


def get_resilience_policy_loader() -> ResiliencePolicyLoader:
    """Get or create resilience policy loader instance."""
    global _policy_loader
    
    if _policy_loader is None:
        policies_path = os.getenv("RESILIENCE_POLICIES_PATH", "/app/policies")
        _policy_loader = ResiliencePolicyLoader(policies_path=policies_path)
    
    return _policy_loader

