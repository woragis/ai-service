"""
Response length limits validation.

Validates response length against configured limits.
"""

from typing import Tuple, Optional
from app.logger import get_logger
from app.quality.policy import get_quality_policy_loader

logger = get_logger()


def validate_length(text: str, agent_name: str = "") -> Tuple[bool, Optional[str]]:
    """
    Validate response length against configured limits.
    
    Args:
        text: Response text to validate
        agent_name: Agent name (for per-agent limits)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.length_limits.enabled:
        return True, None
    
    length = len(text)
    
    # Check per-agent limits first
    if agent_name and agent_name in policy.length_limits.per_agent_limits:
        agent_limits = policy.length_limits.per_agent_limits[agent_name]
        min_length = agent_limits.get("min", policy.length_limits.min_length)
        max_length = agent_limits.get("max", policy.length_limits.max_length)
    else:
        min_length = policy.length_limits.min_length
        max_length = policy.length_limits.max_length
    
    if length < min_length:
        error_msg = f"Response too short: {length} characters (minimum: {min_length})"
        logger.warn("Response length validation failed", length=length, min_length=min_length)
        return False, error_msg
    
    if length > max_length:
        error_msg = f"Response too long: {length} characters (maximum: {max_length})"
        logger.warn("Response length validation failed", length=length, max_length=max_length)
        return False, error_msg
    
    return True, None


def get_length_limits(agent_name: str = "") -> dict:
    """Get current length limits for an agent."""
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    
    if agent_name and agent_name in policy.length_limits.per_agent_limits:
        agent_limits = policy.length_limits.per_agent_limits[agent_name]
        return {
            "min": agent_limits.get("min", policy.length_limits.min_length),
            "max": agent_limits.get("max", policy.length_limits.max_length),
            "enabled": policy.length_limits.enabled,
        }
    
    return {
        "min": policy.length_limits.min_length,
        "max": policy.length_limits.max_length,
        "enabled": policy.length_limits.enabled,
    }

