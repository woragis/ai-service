"""
Retry logic with exponential backoff and configurable strategies.
"""

import asyncio
import time
from typing import Callable, Any, Optional, Type, Tuple
from app.resilience.policy import RetryStrategy
from app.logger import get_logger

logger = get_logger()


def calculate_backoff_delay(attempt: int, strategy: RetryStrategy) -> float:
    """Calculate delay for retry attempt."""
    if strategy.backoff_type == "exponential":
        delay = strategy.initial_delay * (strategy.multiplier ** (attempt - 1))
    elif strategy.backoff_type == "linear":
        delay = strategy.initial_delay * attempt
    else:  # fixed
        delay = strategy.initial_delay
    
    return min(delay, strategy.max_delay)


def is_retryable_error(error: Exception, strategy: RetryStrategy) -> bool:
    """Check if error is retryable based on strategy."""
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    for retryable in strategy.retryable_errors:
        if retryable.lower() in error_str or retryable.lower() in error_type:
            return True
    
    # Default retryable errors
    retryable_types = [
        "timeout", "connection", "rate", "limit", "unavailable",
        "server_error", "internal", "temporary"
    ]
    
    return any(rt in error_str or rt in error_type for rt in retryable_types)


async def retry_with_backoff(
    func: Callable,
    strategy: RetryStrategy,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with retry and backoff.
    
    Args:
        func: Async function to execute
        strategy: Retry strategy configuration
        *args, **kwargs: Arguments for func
    
    Returns:
        Result from func
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(1, strategy.max_attempts + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info("Retry succeeded", attempt=attempt, max_attempts=strategy.max_attempts)
            return result
        except Exception as e:
            last_exception = e
            
            # Check if error is retryable
            if not is_retryable_error(e, strategy):
                logger.warn("Non-retryable error", error=str(e), error_type=type(e).__name__)
                raise
            
            # If this was the last attempt, raise
            if attempt >= strategy.max_attempts:
                logger.error("All retry attempts exhausted", 
                           attempts=attempt, 
                           error=str(e),
                           error_type=type(e).__name__)
                raise
            
            # Calculate and wait for backoff
            delay = calculate_backoff_delay(attempt, strategy)
            logger.warn("Retry attempt failed, backing off", 
                       attempt=attempt,
                       max_attempts=strategy.max_attempts,
                       delay=delay,
                       error=str(e))
            await asyncio.sleep(delay)
    
    # Should not reach here, but just in case
    raise last_exception or Exception("Retry failed")


async def execute_with_resilience(
    func: Callable,
    provider: str,
    strategy: Optional[RetryStrategy] = None,
    enable_retry: bool = True,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with retry and circuit breaker support.
    
    Args:
        func: Async function to execute
        provider: Provider name for circuit breaker
        strategy: Retry strategy (if None, uses default)
        enable_retry: Whether to enable retry
        *args, **kwargs: Arguments for func
    
    Returns:
        Result from func
    """
    from app.resilience.circuit_breaker import get_circuit_breaker_manager
    from app.resilience.policy import get_resilience_policy_loader
    
    policy_loader = get_resilience_policy_loader()
    policy = policy_loader.get_policy()
    
    # Get circuit breaker
    cb_manager = get_circuit_breaker_manager()
    cb_config = policy.circuit_breakers.get(provider, policy.circuit_breakers.get("default"))
    if cb_config:
        breaker = cb_manager.get_breaker(
            provider=provider,
            failure_threshold=cb_config.failure_threshold,
            success_threshold=cb_config.success_threshold,
            timeout=cb_config.timeout,
            half_open_max_calls=cb_config.half_open_max_calls,
        )
        
        # Check if circuit breaker allows the call
        if not breaker.can_attempt():
            logger.warn("Circuit breaker is open, rejecting request", provider=provider)
            raise Exception(f"Circuit breaker is open for provider {provider}")
    
    # Get retry strategy
    if strategy is None:
        strategy = policy.retry_strategies.get(provider) or policy.retry_strategies.get("default")
        if strategy is None:
            strategy = RetryStrategy()  # Use default
    
    # Execute with retry if enabled
    if enable_retry and policy.enable_retry:
        try:
            result = await retry_with_backoff(func, strategy, *args, **kwargs)
            if cb_config:
                breaker.record_success()
            return result
        except Exception as e:
            if cb_config:
                breaker.record_failure()
            raise
    else:
        # Execute without retry
        try:
            result = await func(*args, **kwargs)
            if cb_config:
                breaker.record_success()
            return result
        except Exception as e:
            if cb_config:
                breaker.record_failure()
            raise

