"""
Cost-based routing enhancements.

Enhances routing decisions based on cost estimates and budget constraints.
"""

from typing import Optional, Tuple
from app.logger import get_logger
from app.cost_control.policy import get_cost_control_policy_loader
from app.cost_tracking import estimate_request_cost

logger = get_logger()


def should_use_cheaper_model(
    estimated_cost: float,
    current_model_quality: float = 1.0
) -> bool:
    """
    Determine if a cheaper model should be used based on cost and quality.
    
    Args:
        estimated_cost: Estimated cost for the request
        current_model_quality: Quality score of current model (0-1)
    
    Returns:
        True if cheaper model should be used
    """
    policy = get_cost_control_policy_loader().get_policy()
    
    if not policy.cost_routing.enabled:
        return False
    
    if not policy.cost_routing.prefer_cheaper_models:
        return False
    
    # Use cheaper model if cost exceeds threshold and quality is acceptable
    if estimated_cost > policy.cost_routing.cost_threshold_usd:
        if current_model_quality >= policy.cost_routing.quality_threshold:
            logger.debug("Cost-based routing: prefer cheaper model",
                        estimated_cost=estimated_cost,
                        quality=current_model_quality)
            return True
    
    return False


def estimate_and_check_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int = 0
) -> Tuple[float, bool, Optional[str]]:
    """
    Estimate cost and check against budget limits.
    
    Args:
        provider: Provider name
        model: Model name
        input_tokens: Input token count
        output_tokens: Output token count (estimated if not known)
    
    Returns:
        Tuple of (estimated_cost, allowed, error_message)
    """
    from app.cost_control.budget_tracker import get_budget_tracker
    
    # Estimate cost
    estimated_cost = estimate_request_cost(provider, model, input_tokens, output_tokens)
    
    # Check budget
    budget_tracker = get_budget_tracker()
    allowed, error_msg = budget_tracker.record_spending(estimated_cost)
    
    return estimated_cost, allowed, error_msg


def get_cost_routing_config() -> dict:
    """Get current cost routing configuration."""
    policy = get_cost_control_policy_loader().get_policy()
    return {
        "enabled": policy.cost_routing.enabled,
        "prefer_cheaper_models": policy.cost_routing.prefer_cheaper_models,
        "cost_threshold_usd": policy.cost_routing.cost_threshold_usd,
        "quality_threshold": policy.cost_routing.quality_threshold,
    }

