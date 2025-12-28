"""
Toxicity detection implementation.

Detects toxic content in responses.
"""

import re
from typing import Tuple, Optional, List
from app.logger import get_logger
from app.quality.policy import get_quality_policy_loader

logger = get_logger()


def detect_toxicity(text: str) -> Tuple[float, List[str]]:
    """
    Detect toxicity in text.
    
    Simple keyword-based toxicity detection.
    In production, this could use more sophisticated models like Perspective API.
    
    Args:
        text: Text to analyze
    
    Returns:
        Tuple of (toxicity_score, matched_keywords)
    """
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.toxicity_detection.enabled:
        return 0.0, []
    
    text_lower = text.lower()
    matched_keywords = []
    
    # Check for toxic keywords
    for keyword in policy.toxicity_detection.toxic_keywords:
        if keyword.lower() in text_lower:
            matched_keywords.append(keyword)
    
    # Calculate toxicity score based on matches
    if matched_keywords:
        # Base score from keyword matches
        base_score = min(1.0, len(matched_keywords) * 0.3)
        
        # Check for aggressive patterns
        aggressive_patterns = [
            r"\b(kill|die|death|murder|violence)\b",
            r"\b(hate|hated|hating)\b",
            r"\b(stupid|idiot|moron|dumb)\b",
        ]
        
        pattern_matches = sum(1 for pattern in aggressive_patterns if re.search(pattern, text_lower))
        pattern_score = min(0.5, pattern_matches * 0.2)
        
        toxicity_score = min(1.0, base_score + pattern_score)
        
        logger.warn("Toxicity detected", score=toxicity_score, keywords=matched_keywords)
        return toxicity_score, matched_keywords
    
    return 0.0, []


def check_toxicity(text: str) -> Tuple[bool, Optional[str], float]:
    """
    Check for toxicity and determine if content should be blocked.
    
    Args:
        text: Text to check
    
    Returns:
        Tuple of (allowed, error_message, toxicity_score)
    """
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.toxicity_detection.enabled:
        return True, None, 0.0
    
    toxicity_score, matched_keywords = detect_toxicity(text)
    
    if toxicity_score >= policy.toxicity_detection.threshold:
        if policy.toxicity_detection.action == "block":
            error_msg = f"Content blocked: toxicity detected (score: {toxicity_score:.2f}, threshold: {policy.toxicity_detection.threshold})"
            logger.warn("Content blocked due to toxicity", 
                       score=toxicity_score,
                       threshold=policy.toxicity_detection.threshold,
                       keywords=matched_keywords)
            return False, error_msg, toxicity_score
        elif policy.toxicity_detection.action == "warn":
            logger.warn("Toxicity detected (warning only)", 
                       score=toxicity_score,
                       keywords=matched_keywords)
    
    return True, None, toxicity_score


def sanitize_toxicity(text: str) -> str:
    """
    Sanitize text by removing toxic content.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text
    """
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.toxicity_detection.enabled or policy.toxicity_detection.action != "sanitize":
        return text
    
    sanitized = text
    
    # Remove toxic keywords
    for keyword in policy.toxicity_detection.toxic_keywords:
        sanitized = re.sub(
            re.escape(keyword),
            "[FILTERED]",
            sanitized,
            flags=re.IGNORECASE
        )
    
    return sanitized


def get_toxicity_config() -> dict:
    """Get current toxicity detection configuration."""
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    return {
        "enabled": policy.toxicity_detection.enabled,
        "threshold": policy.toxicity_detection.threshold,
        "action": policy.toxicity_detection.action,
        "toxic_keywords": policy.toxicity_detection.toxic_keywords,
    }

