"""
Response sanitization implementation.

Sanitizes responses to remove potentially dangerous content.
"""

import re
from typing import Optional
from html import escape
from app.logger import get_logger
from app.security.policy import get_security_policy_loader

logger = get_logger()


def sanitize_response(text: str) -> str:
    """
    Sanitize response text.
    
    Args:
        text: Response text to sanitize
    
    Returns:
        Sanitized text
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.response_sanitization.enabled:
        return text
    
    sanitized = text
    
    # Remove script tags
    if policy.response_sanitization.remove_script_tags:
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers
    if policy.response_sanitization.remove_event_handlers:
        sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
    
    # Remove HTML tags (except allowed ones)
    if policy.response_sanitization.remove_html_tags:
        allowed_tags = policy.response_sanitization.allowed_html_tags
        if allowed_tags:
            # Remove all tags except allowed ones
            pattern = r'<(?!\/?(?:' + '|'.join(allowed_tags) + ')\b)[^>]*>'
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        else:
            # Remove all HTML tags
            sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    # Apply length limit
    if policy.response_sanitization.max_length:
        if len(sanitized) > policy.response_sanitization.max_length:
            sanitized = sanitized[:policy.response_sanitization.max_length]
            logger.warn("Response truncated due to max_length", 
                       original_length=len(text),
                       max_length=policy.response_sanitization.max_length)
    
    return sanitized

