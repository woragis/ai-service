"""
Feature flags module.

Provides feature toggles for RAG, streaming, providers, and custom features.
"""

from .policy import get_feature_policy_loader, FeaturePolicy
from .flags import (
    is_rag_enabled,
    is_streaming_enabled,
    is_provider_enabled,
    is_feature_enabled,
    get_feature_config,
)

__all__ = [
    "get_feature_policy_loader",
    "FeaturePolicy",
    "is_rag_enabled",
    "is_streaming_enabled",
    "is_provider_enabled",
    "is_feature_enabled",
    "get_feature_config",
]

