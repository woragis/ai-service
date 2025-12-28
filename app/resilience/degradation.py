"""
Graceful degradation logic.
"""

import time
from typing import Optional, Dict, Any, Tuple
from app.resilience.policy import get_resilience_policy_loader, GracefulDegradationRule
from app.logger import get_logger

logger = get_logger()


def check_degradation_conditions(
    error: Optional[Exception] = None,
    latency_ms: Optional[float] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    """
    Check if graceful degradation should be applied.
    
    Returns:
        Tuple of (action, fallback_provider, fallback_model) or None
    """
    policy_loader = get_resilience_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.enable_graceful_degradation:
        return None
    
    for rule in policy.degradation_rules:
        should_apply = False
        
        # Check condition
        if rule.condition == "error_type":
            if error:
                error_str = str(error).lower()
                error_type = type(error).__name__.lower()
                threshold_str = str(rule.threshold).lower()
                should_apply = threshold_str in error_str or threshold_str in error_type
        
        elif rule.condition == "latency_threshold":
            if latency_ms is not None and rule.max_latency:
                should_apply = latency_ms > rule.max_latency
        
        elif rule.condition == "provider_failure":
            if provider and rule.threshold:
                # Could check circuit breaker state here
                should_apply = True  # Simplified
        
        if should_apply:
            logger.info("Applying graceful degradation", 
                       condition=rule.condition,
                       action=rule.action,
                       fallback_provider=rule.fallback_provider)
            return (rule.action, rule.fallback_provider, rule.fallback_model)
    
    return None


def apply_degradation(
    action: str,
    current_provider: str,
    current_model: Optional[str],
    fallback_provider: Optional[str] = None,
    fallback_model: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """
    Apply graceful degradation action.
    
    Returns:
        Tuple of (provider, model) to use
    """
    if action == "downgrade_model":
        # Use a cheaper/faster model from same provider
        if current_provider == "openai" and current_model != "gpt-4o-mini":
            return (current_provider, "gpt-4o-mini")
        elif current_provider == "anthropic" and current_model != "claude-3-haiku":
            return (current_provider, "claude-3-haiku")
        # Keep current if already at lowest tier
        return (current_provider, current_model)
    
    elif action == "use_fallback":
        if fallback_provider:
            return (fallback_provider, fallback_model)
        # Default fallbacks
        if current_provider == "openai":
            return ("anthropic", "claude-3-haiku")
        elif current_provider == "anthropic":
            return ("openai", "gpt-4o-mini")
        return (current_provider, current_model)
    
    elif action == "return_cached":
        # This would need cache integration
        logger.info("Degradation: return cached response (not implemented)")
        return (current_provider, current_model)
    
    # Default: no change
    return (current_provider, current_model)

