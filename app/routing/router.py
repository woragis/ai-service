"""
Model selection and routing logic.

Implements provider selection, fallback chains, query complexity detection,
and cost/quality trade-offs based on routing policies.
"""

import time
from typing import Optional, Tuple, List
from app.routing.policy import get_routing_policy_loader, RoutingPolicy, ProviderConfig
from app.logger import get_logger

logger = get_logger()


def detect_query_complexity(query: str, agent_name: str = "") -> str:
    """
    Detect query complexity based on query text and agent.
    
    Returns: "simple", "medium", or "complex"
    """
    query_lower = query.lower()
    query_length = len(query)
    word_count = len(query.split())
    
    # Simple heuristics for complexity
    if query_length < 50 or word_count < 10:
        return "simple"
    
    # Complex indicators
    complex_indicators = [
        "analyze", "compare", "evaluate", "design", "architecture",
        "strategy", "optimize", "implement", "refactor", "migrate",
        "scalable", "distributed", "microservices", "performance",
    ]
    
    if any(indicator in query_lower for indicator in complex_indicators):
        return "complex"
    
    if query_length > 500 or word_count > 100:
        return "complex"
    
    return "medium"


def select_provider_and_model(
    requested_provider: Optional[str] = None,
    requested_model: Optional[str] = None,
    query: str = "",
    agent_name: str = "",
    cost_mode: str = "balanced",
    enable_fallback: bool = True,
) -> Tuple[str, Optional[str], List[str]]:
    """
    Select provider and model based on routing policies.
    
    Args:
        requested_provider: User-requested provider (if any)
        requested_model: User-requested model (if any)
        query: User query text
        agent_name: Agent name
        cost_mode: Cost mode ("cost_optimized", "balanced", "quality_optimized")
        enable_fallback: Whether to return fallback chain
    
    Returns:
        Tuple of (provider, model, fallback_chain)
    """
    policy_loader = get_routing_policy_loader()
    policy = policy_loader.get_policy()
    
    # If provider/model explicitly requested and enabled, use it
    if requested_provider:
        provider_lower = requested_provider.lower()
        if provider_lower in policy.providers:
            provider_config = policy.providers[provider_lower]
            if provider_config.enabled:
                model = requested_model or provider_config.models[0] if provider_config.models else None
                fallback_chain = _get_fallback_chain(provider_lower, policy) if enable_fallback else []
                return (provider_lower, model, fallback_chain)
    
    # Auto-routing based on policies
    if not policy.enable_auto_routing:
        # Use default
        default_provider = policy.default_provider
        provider_config = policy.providers.get(default_provider)
        model = requested_model or policy.default_model or (provider_config.models[0] if provider_config and provider_config.models else None)
        fallback_chain = _get_fallback_chain(default_provider, policy) if enable_fallback else []
        return (default_provider, model, fallback_chain)
    
    # Detect query complexity
    complexity = detect_query_complexity(query, agent_name)
    
    # Apply complexity rules
    provider, model = _apply_complexity_rules(complexity, policy, requested_model)
    if provider:
        fallback_chain = _get_fallback_chain(provider, policy) if enable_fallback else []
        return (provider, model, fallback_chain)
    
    # Apply cost/quality trade-offs
    provider, model = _apply_cost_quality_tradeoff(cost_mode, policy, requested_model)
    if provider:
        fallback_chain = _get_fallback_chain(provider, policy) if enable_fallback else []
        return (provider, model, fallback_chain)
    
    # Fallback to default
    default_provider = policy.default_provider
    provider_config = policy.providers.get(default_provider)
    model = requested_model or policy.default_model or (provider_config.models[0] if provider_config and provider_config.models else None)
    fallback_chain = _get_fallback_chain(default_provider, policy) if enable_fallback else []
    return (default_provider, model, fallback_chain)


def _apply_complexity_rules(
    complexity: str,
    policy: RoutingPolicy,
    requested_model: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Apply complexity-based routing rules."""
    for rule in policy.complexity_rules:
        if rule.complexity == complexity:
            # Use first available provider from preference list
            for provider_name in rule.provider_preference:
                provider_config = policy.providers.get(provider_name)
                if provider_config and provider_config.enabled:
                    # Check if model preference exists
                    model = rule.model_preference.get(provider_name)
                    if not model:
                        model = requested_model or (provider_config.models[0] if provider_config.models else None)
                    return (provider_name, model)
    
    return (None, None)


def _apply_cost_quality_tradeoff(
    cost_mode: str,
    policy: RoutingPolicy,
    requested_model: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Apply cost/quality trade-off rules."""
    cq = policy.cost_quality
    
    # Use mode from parameter or policy default
    mode = cost_mode if cost_mode in ["cost_optimized", "balanced", "quality_optimized"] else cq.mode
    
    # Check provider mapping for this mode
    if mode in cq.provider_mapping:
        provider_map = cq.provider_mapping[mode]
        for provider_name, model_name in provider_map.items():
            provider_config = policy.providers.get(provider_name)
            if provider_config and provider_config.enabled:
                return (provider_name, model_name or requested_model)
    
    # Fallback to priority-based selection
    if mode == "cost_optimized":
        # Select provider with lowest cost tier
        providers_by_cost = sorted(
            [(name, config) for name, config in policy.providers.items() if config.enabled],
            key=lambda x: {"low": 1, "medium": 2, "high": 3}.get(x[1].cost_tier, 2)
        )
    elif mode == "quality_optimized":
        # Select provider with highest quality tier
        providers_by_cost = sorted(
            [(name, config) for name, config in policy.providers.items() if config.enabled],
            key=lambda x: {"low": 3, "medium": 2, "high": 1}.get(x[1].quality_tier, 2)
        )
    else:  # balanced
        # Select by priority
        providers_by_cost = sorted(
            [(name, config) for name, config in policy.providers.items() if config.enabled],
            key=lambda x: x[1].priority
        )
    
    if providers_by_cost:
        provider_name, provider_config = providers_by_cost[0]
        model = requested_model or (provider_config.models[0] if provider_config.models else None)
        return (provider_name, model)
    
    return (None, None)


def _get_fallback_chain(provider: str, policy: RoutingPolicy) -> List[str]:
    """Get fallback chain for a provider."""
    for chain in policy.fallback_chains:
        if chain.primary == provider:
            return chain.fallbacks
    
    # Default fallback: try other enabled providers
    fallbacks = [
        name for name, config in policy.providers.items()
        if name != provider and config.enabled
    ]
    return fallbacks


async def execute_with_fallback(
    provider: str,
    model: Optional[str],
    fallback_chain: List[str],
    execute_fn,
    endpoint: Optional[str] = None,
    *args,
    **kwargs
):
    """
    Execute a function with fallback chain support and resilience features.
    
    Args:
        provider: Primary provider
        model: Model name
        fallback_chain: List of fallback providers
        execute_fn: Async function to execute (provider, model, *args, **kwargs)
        endpoint: Endpoint name for timeout lookup
        *args, **kwargs: Additional arguments for execute_fn
    
    Returns:
        Result from execute_fn
    
    Raises:
        Last exception if all providers fail
    """
    from app.resilience import (
        execute_with_resilience,
        execute_with_timeout,
        check_degradation_conditions,
        apply_degradation,
    )
    from app.resilience.policy import get_resilience_policy_loader
    
    policy_loader = get_resilience_policy_loader()
    policy = policy_loader.get_policy()
    
    providers_to_try = [provider] + fallback_chain
    last_exception = None
    start_time = time.time()
    
    # Get circuit breaker manager
    from app.resilience.circuit_breaker import get_circuit_breaker_manager
    cb_manager = get_circuit_breaker_manager()
    
    for attempt_provider in providers_to_try:
        breaker = None
        cb_config = None
        try:
            logger.info("Attempting provider", provider=attempt_provider, model=model)
            
            # Check circuit breaker
            cb_config = policy.circuit_breakers.get(attempt_provider)
            if cb_config and policy.enable_circuit_breaker:
                breaker = cb_manager.get_breaker(
                    provider=attempt_provider,
                    failure_threshold=cb_config.failure_threshold,
                    success_threshold=cb_config.success_threshold,
                    timeout=cb_config.timeout,
                    half_open_max_calls=cb_config.half_open_max_calls,
                )
                if not breaker.can_attempt():
                    logger.warn("Circuit breaker is open, skipping provider", provider=attempt_provider)
                    continue
            
            # Execute with timeout and retry
            async def _execute_with_timeout_and_retry():
                return await execute_with_resilience(
                    execute_fn,
                    attempt_provider,
                    strategy=policy.retry_strategies.get(attempt_provider),
                    enable_retry=policy.enable_retry,
                    *(model, *args),
                    **kwargs
                )
            
            result = await execute_with_timeout(
                _execute_with_timeout_and_retry,
                provider=attempt_provider,
                model=model,
                endpoint=endpoint,
            )
            
            # Record success in circuit breaker
            if breaker and policy.enable_circuit_breaker:
                breaker.record_success()
            
            if attempt_provider != provider:
                logger.info("Fallback provider succeeded", original=provider, fallback=attempt_provider)
            return result
            
        except Exception as e:
            last_exception = e
            latency_ms = (time.time() - start_time) * 1000
            
            # Record failure in circuit breaker
            if breaker and policy.enable_circuit_breaker:
                breaker.record_failure()
            
            # Check for graceful degradation
            if policy.enable_graceful_degradation:
                degradation = check_degradation_conditions(
                    error=e,
                    latency_ms=latency_ms,
                    provider=attempt_provider,
                    model=model,
                )
                if degradation:
                    action, fallback_provider, fallback_model = degradation
                    if fallback_provider and fallback_provider in providers_to_try:
                        # Apply degradation and continue with fallback
                        logger.info("Applying graceful degradation", 
                                   action=action,
                                   from_provider=attempt_provider,
                                   to_provider=fallback_provider)
                        continue
            
            logger.warn("Provider failed, trying fallback", provider=attempt_provider, error=str(e))
            continue
    
    # All providers failed
    logger.error("All providers failed", providers=providers_to_try)
    raise last_exception or Exception("All providers failed")

