"""
Security and content policy definitions and loader.

Defines content filtering, PII detection, response sanitization, and prompt injection detection.
"""

import os
import yaml
import re
from typing import Dict, Any, Optional, List, Pattern
from pathlib import Path
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


@dataclass
class ContentFilterConfig:
    """Content filtering configuration."""
    enabled: bool = True
    blocked_patterns: List[str] = field(default_factory=lambda: [
        r"<script[^>]*>.*?</script>",  # XSS attempts
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
        r"eval\s*\(",  # eval() calls
        r"exec\s*\(",  # exec() calls
    ])
    blocked_keywords: List[str] = field(default_factory=lambda: [
        "malware",
        "virus",
        "exploit",
        "hack",
    ])
    action: str = "block"  # "block", "warn", "sanitize"


@dataclass
class PIIDetectionConfig:
    """PII detection and masking configuration."""
    enabled: bool = True
    detect_email: bool = True
    detect_phone: bool = True
    detect_ssn: bool = True
    detect_credit_card: bool = True
    detect_ip_address: bool = True
    mask_char: str = "*"
    action: str = "mask"  # "mask", "block", "warn"


@dataclass
class ResponseSanitizationConfig:
    """Response sanitization configuration."""
    enabled: bool = True
    remove_html_tags: bool = True
    remove_script_tags: bool = True
    remove_event_handlers: bool = True
    max_length: Optional[int] = None  # None = no limit
    allowed_html_tags: List[str] = field(default_factory=lambda: ["p", "br", "strong", "em"])


@dataclass
class PromptInjectionConfig:
    """Prompt injection detection configuration."""
    enabled: bool = True
    suspicious_patterns: List[str] = field(default_factory=lambda: [
        r"ignore\s+(previous|above|all)\s+instructions?",
        r"forget\s+(everything|all|previous)",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"system\s*:\s*",
        r"<\|system\|>",
        r"\[SYSTEM\]",
        r"override",
        r"bypass",
    ])
    action: str = "block"  # "block", "warn", "sanitize"
    threshold: float = 0.5  # Minimum confidence to trigger (0-1)


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    version: str = "1.0.0"
    content_filter: ContentFilterConfig = field(default_factory=ContentFilterConfig)
    pii_detection: PIIDetectionConfig = field(default_factory=PIIDetectionConfig)
    response_sanitization: ResponseSanitizationConfig = field(default_factory=ResponseSanitizationConfig)
    prompt_injection: PromptInjectionConfig = field(default_factory=PromptInjectionConfig)


class SecurityPolicyLoader:
    """Loads and manages security policies from YAML files."""
    
    def __init__(self, policies_path: str = "/app/policies"):
        self.policies_path = Path(policies_path)
        self.logger = get_logger()
        self._policy: Optional[SecurityPolicy] = None
        self._compiled_patterns: Dict[str, List[Pattern]] = {}
        self._load_policy()
    
    def _load_policy(self):
        """Load policy from YAML file."""
        policy_file = self.policies_path / "security.yaml"
        
        if not policy_file.exists():
            self.logger.warn("Security policy file not found, using defaults", path=str(policy_file))
            self._policy = SecurityPolicy()
            self._compile_patterns()
            return
        
        try:
            with open(policy_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "security" not in data:
                raise ValueError("Invalid security policy structure: missing 'security' key")
            
            security_data = data["security"]
            
            policy = SecurityPolicy(
                version=data.get("version", "1.0.0"),
                content_filter=ContentFilterConfig(**security_data.get("content_filter", {})),
                pii_detection=PIIDetectionConfig(**security_data.get("pii_detection", {})),
                response_sanitization=ResponseSanitizationConfig(**security_data.get("response_sanitization", {})),
                prompt_injection=PromptInjectionConfig(**security_data.get("prompt_injection", {})),
            )
            
            self._policy = policy
            self._compile_patterns()
            self.logger.info("Security policy loaded", file=str(policy_file))
        except Exception as e:
            self.logger.error("Failed to load security policy", error=str(e), file=str(policy_file))
            self._policy = SecurityPolicy()  # Fallback to defaults
            self._compile_patterns()
            self.logger.info("Default security policy loaded due to error")
    
    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        if not self._policy:
            return
        
        self._compiled_patterns = {
            "content_filter": [
                re.compile(pattern, re.IGNORECASE | re.DOTALL)
                for pattern in self._policy.content_filter.blocked_patterns
            ],
            "prompt_injection": [
                re.compile(pattern, re.IGNORECASE)
                for pattern in self._policy.prompt_injection.suspicious_patterns
            ],
        }
    
    def get_policy(self) -> SecurityPolicy:
        """Get the current policy."""
        if self._policy is None:
            self._load_policy()
        return self._policy if self._policy else SecurityPolicy()
    
    def get_compiled_patterns(self) -> Dict[str, List[Pattern]]:
        """Get compiled regex patterns."""
        return self._compiled_patterns
    
    def reload(self):
        """Reload policy from file (hot reload)."""
        self._policy = None
        self._compiled_patterns = {}
        self._load_policy()
        self.logger.info("Security policies reloaded")


_policy_loader: Optional[SecurityPolicyLoader] = None


def get_security_policy_loader() -> SecurityPolicyLoader:
    """Get the global security policy loader instance."""
    global _policy_loader
    if _policy_loader is None:
        policies_path = os.getenv("SECURITY_POLICIES_PATH", "/app/policies")
        _policy_loader = SecurityPolicyLoader(policies_path=policies_path)
    return _policy_loader

