"""
Quality and validation policy definitions and loader.

Defines response length limits, output format validation, quality checks, and toxicity detection.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


@dataclass
class LengthLimitConfig:
    """Response length limits configuration."""
    enabled: bool = True
    min_length: int = 10  # Minimum response length in characters
    max_length: int = 50000  # Maximum response length in characters
    per_agent_limits: Dict[str, Dict[str, int]] = field(default_factory=dict)  # agent_name -> {min, max}


@dataclass
class FormatValidationConfig:
    """Output format validation configuration."""
    enabled: bool = True
    allowed_formats: List[str] = field(default_factory=lambda: ["text", "json", "markdown"])
    required_format: Optional[str] = None  # If set, response must match this format
    validate_json: bool = True  # Validate JSON format if JSON is detected
    validate_markdown: bool = False  # Basic markdown validation


@dataclass
class QualityCheckConfig:
    """Quality checks configuration."""
    enabled: bool = True
    check_coherence: bool = True  # Check if response is coherent
    check_relevance: bool = True  # Check if response is relevant to query
    coherence_threshold: float = 0.5  # Minimum coherence score (0-1)
    relevance_threshold: float = 0.5  # Minimum relevance score (0-1)
    use_semantic_similarity: bool = True  # Use semantic similarity for relevance


@dataclass
class ToxicityDetectionConfig:
    """Toxicity detection configuration."""
    enabled: bool = True
    threshold: float = 0.7  # Minimum toxicity score to trigger (0-1)
    action: str = "block"  # "block", "warn", "sanitize"
    toxic_keywords: List[str] = field(default_factory=lambda: [
        "hate", "violence", "discrimination", "harassment"
    ])


@dataclass
class QualityPolicy:
    """Quality policy configuration."""
    version: str = "1.0.0"
    length_limits: LengthLimitConfig = field(default_factory=LengthLimitConfig)
    format_validation: FormatValidationConfig = field(default_factory=FormatValidationConfig)
    quality_checks: QualityCheckConfig = field(default_factory=QualityCheckConfig)
    toxicity_detection: ToxicityDetectionConfig = field(default_factory=ToxicityDetectionConfig)


class QualityPolicyLoader:
    """Loads and manages quality policies from YAML files."""
    
    def __init__(self, policies_path: str = "/app/policies")
        self.policies_path = Path(policies_path)
        self.logger = get_logger()
        self._policy: Optional[QualityPolicy] = None
        self._load_policy()
    
    def _load_policy(self):
        """Load policy from YAML file."""
        policy_file = self.policies_path / "quality.yaml"
        
        if not policy_file.exists():
            self.logger.warn("Quality policy file not found, using defaults", path=str(policy_file))
            self._policy = QualityPolicy()
            return
        
        try:
            with open(policy_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "quality" not in data:
                raise ValueError("Invalid quality policy structure: missing 'quality' key")
            
            quality_data = data["quality"]
            
            policy = QualityPolicy(
                version=data.get("version", "1.0.0"),
                length_limits=LengthLimitConfig(**quality_data.get("length_limits", {})),
                format_validation=FormatValidationConfig(**quality_data.get("format_validation", {})),
                quality_checks=QualityCheckConfig(**quality_data.get("quality_checks", {})),
                toxicity_detection=ToxicityDetectionConfig(**quality_data.get("toxicity_detection", {})),
            )
            
            self._policy = policy
            self.logger.info("Quality policy loaded", file=str(policy_file))
        except Exception as e:
            self.logger.error("Failed to load quality policy", error=str(e), file=str(policy_file))
            self._policy = QualityPolicy()  # Fallback to defaults
            self.logger.info("Default quality policy loaded due to error")
    
    def get_policy(self) -> QualityPolicy:
        """Get the current policy."""
        if self._policy is None:
            self._load_policy()
        return self._policy if self._policy else QualityPolicy()
    
    def reload(self):
        """Reload policy from file (hot reload)."""
        self._policy = None
        self._load_policy()
        self.logger.info("Quality policies reloaded")


_policy_loader: Optional[QualityPolicyLoader] = None


def get_quality_policy_loader() -> QualityPolicyLoader:
    """Get the global quality policy loader instance."""
    global _policy_loader
    if _policy_loader is None:
        policies_path = os.getenv("QUALITY_POLICIES_PATH", "/app/policies")
        _policy_loader = QualityPolicyLoader(policies_path=policies_path)
    return _policy_loader

