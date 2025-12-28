"""
Output format validation.

Validates response format (JSON, Markdown, etc.).
"""

import json
import re
from typing import Tuple, Optional, List
from app.logger import get_logger
from app.quality.policy import get_quality_policy_loader

logger = get_logger()


def detect_format(text: str) -> str:
    """
    Detect the format of the response.
    
    Returns:
        Format type: "json", "markdown", or "text"
    """
    text_stripped = text.strip()
    
    # Check for JSON
    if text_stripped.startswith("{") or text_stripped.startswith("["):
        try:
            json.loads(text_stripped)
            return "json"
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Check for Markdown (simple heuristic: contains markdown patterns)
    markdown_patterns = [
        r"^#{1,6}\s+",  # Headers
        r"\*\*.*?\*\*",  # Bold
        r"\*.*?\*",  # Italic
        r"\[.*?\]\(.*?\)",  # Links
        r"```",  # Code blocks
    ]
    
    for pattern in markdown_patterns:
        if re.search(pattern, text, re.MULTILINE):
            return "markdown"
    
    return "text"


def validate_format(text: str) -> Tuple[bool, Optional[str], str]:
    """
    Validate response format.
    
    Args:
        text: Response text to validate
    
    Returns:
        Tuple of (is_valid, error_message, detected_format)
    """
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.format_validation.enabled:
        return True, None, "text"
    
    detected_format = detect_format(text)
    
    # Check if format is allowed
    if detected_format not in policy.format_validation.allowed_formats:
        error_msg = f"Format '{detected_format}' not allowed. Allowed formats: {', '.join(policy.format_validation.allowed_formats)}"
        logger.warn("Format validation failed", detected_format=detected_format, allowed_formats=policy.format_validation.allowed_formats)
        return False, error_msg, detected_format
    
    # Check required format
    if policy.format_validation.required_format:
        if detected_format != policy.format_validation.required_format:
            error_msg = f"Required format '{policy.format_validation.required_format}' not matched. Detected: '{detected_format}'"
            logger.warn("Format validation failed", required=policy.format_validation.required_format, detected=detected_format)
            return False, error_msg, detected_format
    
    # Validate JSON if detected
    if detected_format == "json" and policy.format_validation.validate_json:
        try:
            json.loads(text.strip())
        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.warn("JSON validation failed", error=str(e))
            return False, error_msg, detected_format
    
    # Basic markdown validation (check for balanced code blocks)
    if detected_format == "markdown" and policy.format_validation.validate_markdown:
        code_block_count = text.count("```")
        if code_block_count % 2 != 0:
            error_msg = "Unbalanced markdown code blocks"
            logger.warn("Markdown validation failed", code_blocks=code_block_count)
            return False, error_msg, detected_format
    
    return True, None, detected_format


def get_format_config() -> dict:
    """Get current format validation configuration."""
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    return {
        "enabled": policy.format_validation.enabled,
        "allowed_formats": policy.format_validation.allowed_formats,
        "required_format": policy.format_validation.required_format,
        "validate_json": policy.format_validation.validate_json,
        "validate_markdown": policy.format_validation.validate_markdown,
    }

