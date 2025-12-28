"""
Content filtering implementation.

Filters and blocks content based on configured patterns and keywords.
"""

import re
from typing import Tuple, Optional, List
from app.logger import get_logger
from app.security.policy import get_security_policy_loader

logger = get_logger()


def check_content_filter(text: str) -> Tuple[bool, Optional[str]]:
    """
    Check if content should be blocked based on filtering rules.
    
    Args:
        text: Text to check
    
    Returns:
        Tuple of (allowed, error_message)
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.content_filter.enabled:
        return True, None
    
    text_lower = text.lower()
    
    # Check blocked keywords
    for keyword in policy.content_filter.blocked_keywords:
        if keyword.lower() in text_lower:
            error_msg = f"Content blocked: contains blocked keyword '{keyword}'"
            logger.warn("Content blocked by keyword", keyword=keyword)
            return False, error_msg
    
    # Check blocked patterns
    compiled_patterns = policy_loader.get_compiled_patterns().get("content_filter", [])
    for pattern in compiled_patterns:
        if pattern.search(text):
            error_msg = f"Content blocked: matches blocked pattern"
            logger.warn("Content blocked by pattern", pattern=pattern.pattern)
            return False, error_msg
    
    return True, None


def sanitize_content(text: str) -> str:
    """
    Sanitize content by removing dangerous patterns.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.content_filter.enabled or policy.content_filter.action != "sanitize":
        return text
    
    sanitized = text
    
    # Remove blocked patterns
    compiled_patterns = policy_loader.get_compiled_patterns().get("content_filter", [])
    for pattern in compiled_patterns:
        sanitized = pattern.sub("", sanitized)
    
    # Remove blocked keywords (replace with placeholder)
    for keyword in policy.content_filter.blocked_keywords:
        sanitized = re.sub(
            re.escape(keyword),
            "[FILTERED]",
            sanitized,
            flags=re.IGNORECASE
        )
    
    return sanitized

