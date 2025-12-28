"""
Feature flag checks and utilities.

Provides functions to check if features are enabled.
"""

from typing import Optional
from app.logger import get_logger
from app.features.policy import get_feature_policy_loader

logger = get_logger()


def is_rag_enabled(agent_name: str = "") -> bool:
    """
    Check if RAG is enabled for an agent.
    
    Args:
        agent_name: Agent name
    
    Returns:
        True if RAG is enabled for this agent
    """
    policy_loader = get_feature_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.features.rag.enabled:
        return False
    
    # Check per-agent setting
    if agent_name and agent_name in policy.features.rag.per_agent_enabled:
        return policy.features.rag.per_agent_enabled[agent_name]
    
    # Use default
    return policy.features.rag.default_enabled


def is_streaming_enabled(endpoint: str = "/v1/chat/stream") -> bool:
    """
    Check if streaming is enabled for an endpoint.
    
    Args:
        endpoint: Endpoint path
    
    Returns:
        True if streaming is enabled for this endpoint
    """
    policy_loader = get_feature_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.features.streaming.enabled:
        return False
    
    # Check per-endpoint setting
    if endpoint in policy.features.streaming.per_endpoint_enabled:
        return policy.features.streaming.per_endpoint_enabled[endpoint]
    
    # Default: enabled
    return True


def is_provider_enabled(provider: str) -> bool:
    """
    Check if a provider is enabled.
    
    Args:
        provider: Provider name
    
    Returns:
        True if provider is enabled
    """
    policy_loader = get_feature_policy_loader()
    policy = policy_loader.get_policy()
    
    provider_lower = provider.lower()
    
    # Check disabled list first
    if provider_lower in [p.lower() for p in policy.features.providers.disabled_providers]:
        return False
    
    # Check enabled list
    if policy.features.providers.enabled_providers:
        return provider_lower in [p.lower() for p in policy.features.providers.enabled_providers]
    
    # Default: enabled if not explicitly disabled
    return True


def is_feature_enabled(feature_name: str) -> bool:
    """
    Check if a custom feature flag is enabled.
    
    Args:
        feature_name: Custom feature name
    
    Returns:
        True if feature is enabled
    """
    policy_loader = get_feature_policy_loader()
    policy = policy_loader.get_policy()
    
    return policy.features.custom_flags.get(feature_name, False)


def get_feature_config() -> dict:
    """Get current feature flags configuration."""
    policy_loader = get_feature_policy_loader()
    policy = policy_loader.get_policy()
    return {
        "rag": {
            "enabled": policy.features.rag.enabled,
            "default_enabled": policy.features.rag.default_enabled,
            "per_agent_enabled": policy.features.rag.per_agent_enabled,
        },
        "streaming": {
            "enabled": policy.features.streaming.enabled,
            "per_endpoint_enabled": policy.features.streaming.per_endpoint_enabled,
        },
        "providers": {
            "enabled_providers": policy.features.providers.enabled_providers,
            "disabled_providers": policy.features.providers.disabled_providers,
        },
        "custom_flags": policy.features.custom_flags,
    }

