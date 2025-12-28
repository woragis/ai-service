"""
Prompt injection detection implementation.

Detects and prevents prompt injection attacks.
"""

import re
from typing import Tuple, Optional, List
from app.logger import get_logger
from app.security.policy import get_security_policy_loader

logger = get_logger()


def detect_prompt_injection(text: str) -> Tuple[bool, float, Optional[str]]:
    """
    Detect prompt injection attempts in text.
    
    Args:
        text: Text to analyze
    
    Returns:
        Tuple of (is_injection, confidence, matched_pattern)
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.prompt_injection.enabled:
        return False, 0.0, None
    
    text_lower = text.lower()
    matches = []
    
    # Check suspicious patterns
    compiled_patterns = policy_loader.get_compiled_patterns().get("prompt_injection", [])
    for pattern in compiled_patterns:
        if pattern.search(text_lower):
            matches.append(pattern.pattern)
    
    if matches:
        # Calculate confidence based on number of matches
        confidence = min(1.0, len(matches) * 0.3)  # Each match adds 0.3 confidence
        
        if confidence >= policy.prompt_injection.threshold:
            matched_pattern = matches[0]  # Return first match
            logger.warn("Prompt injection detected", 
                       confidence=confidence,
                       pattern=matched_pattern,
                       matches=len(matches))
            return True, confidence, matched_pattern
    
    return False, 0.0, None


def check_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """
    Check for prompt injection and determine if content should be blocked.
    
    Args:
        text: Text to check
    
    Returns:
        Tuple of (allowed, error_message)
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.prompt_injection.enabled:
        return True, None
    
    is_injection, confidence, matched_pattern = detect_prompt_injection(text)
    
    if is_injection and policy.prompt_injection.action == "block":
        error_msg = f"Content blocked: potential prompt injection detected (confidence: {confidence:.2f})"
        logger.warn("Content blocked due to prompt injection", 
                   confidence=confidence,
                   pattern=matched_pattern)
        return False, error_msg
    
    if is_injection and policy.prompt_injection.action == "warn":
        logger.warn("Prompt injection detected (warning only)", 
                   confidence=confidence,
                   pattern=matched_pattern)
    
    return True, None


def sanitize_prompt_injection(text: str) -> str:
    """
    Sanitize text to remove prompt injection patterns.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.prompt_injection.enabled or policy.prompt_injection.action != "sanitize":
        return text
    
    sanitized = text
    
    # Remove suspicious patterns
    compiled_patterns = policy_loader.get_compiled_patterns().get("prompt_injection", [])
    for pattern in compiled_patterns:
        sanitized = pattern.sub("[FILTERED]", sanitized)
    
    return sanitized

