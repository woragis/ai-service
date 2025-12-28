"""
Token usage limit enforcement.

Validates and enforces token limits per request.
"""

from typing import Tuple, Optional
from app.logger import get_logger
from app.cost_control.policy import get_cost_control_policy_loader

logger = get_logger()


def validate_token_limits(
    input_tokens: int,
    output_tokens: int = 0,
    estimated_total: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate token usage against configured limits.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens (if known)
        estimated_total: Estimated total tokens (if known)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    policy = get_cost_control_policy_loader().get_policy()
    
    if not policy.token_limits.enabled:
        return True, None
    
    # Check input token limit
    if input_tokens > policy.token_limits.max_input_tokens:
        error_msg = (
            f"Input token count {input_tokens} exceeds limit "
            f"{policy.token_limits.max_input_tokens}"
        )
        logger.warn("Token limit exceeded", 
                   input_tokens=input_tokens, 
                   limit=policy.token_limits.max_input_tokens)
        return False, error_msg
    
    # Check output token limit
    if output_tokens > policy.token_limits.max_output_tokens:
        error_msg = (
            f"Output token count {output_tokens} exceeds limit "
            f"{policy.token_limits.max_output_tokens}"
        )
        logger.warn("Token limit exceeded",
                   output_tokens=output_tokens,
                   limit=policy.token_limits.max_output_tokens)
        return False, error_msg
    
    # Check total token limit
    total_tokens = input_tokens + output_tokens
    if estimated_total:
        total_tokens = estimated_total
    
    if total_tokens > policy.token_limits.max_total_tokens:
        error_msg = (
            f"Total token count {total_tokens} exceeds limit "
            f"{policy.token_limits.max_total_tokens}"
        )
        logger.warn("Token limit exceeded",
                   total_tokens=total_tokens,
                   limit=policy.token_limits.max_total_tokens)
        return False, error_msg
    
    return True, None


def get_token_limits() -> dict:
    """Get current token limits configuration."""
    policy = get_cost_control_policy_loader().get_policy()
    return {
        "max_input_tokens": policy.token_limits.max_input_tokens,
        "max_output_tokens": policy.token_limits.max_output_tokens,
        "max_total_tokens": policy.token_limits.max_total_tokens,
        "enabled": policy.token_limits.enabled,
    }

