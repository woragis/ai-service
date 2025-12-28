"""
Timeout management per provider, model, and endpoint.
"""

import asyncio
from typing import Optional, Callable, Any
from app.resilience.policy import get_resilience_policy_loader, TimeoutConfig
from app.logger import get_logger

logger = get_logger()


def get_timeout(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> float:
    """
    Get timeout value based on provider, model, and endpoint.
    
    Returns timeout in seconds.
    """
    policy_loader = get_resilience_policy_loader()
    policy = policy_loader.get_policy()
    timeouts = policy.timeouts
    
    # Check endpoint-specific timeout
    if endpoint and endpoint in timeouts.per_endpoint:
        return timeouts.per_endpoint[endpoint]
    
    # Check model-specific timeout
    if model and model in timeouts.per_model:
        return timeouts.per_model[model]
    
    # Check provider-specific timeout
    if provider and provider in timeouts.per_provider:
        return timeouts.per_provider[provider]
    
    # Return default
    return timeouts.default


async def execute_with_timeout(
    func: Callable,
    timeout: Optional[float] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    endpoint: Optional[str] = None,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with timeout.
    
    Args:
        func: Async function to execute
        timeout: Explicit timeout (if None, uses policy)
        provider: Provider name for timeout lookup
        model: Model name for timeout lookup
        endpoint: Endpoint name for timeout lookup
        *args, **kwargs: Arguments for func
    
    Returns:
        Result from func
    
    Raises:
        asyncio.TimeoutError if timeout is exceeded
    """
    if timeout is None:
        timeout = get_timeout(provider=provider, model=model, endpoint=endpoint)
    
    try:
        result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.error("Request timeout exceeded", 
                    timeout=timeout, 
                    provider=provider, 
                    model=model,
                    endpoint=endpoint)
        raise TimeoutError(f"Request exceeded timeout of {timeout}s")

