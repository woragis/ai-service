"""
Agent policy loader and validator.

Loads agent policies from YAML files and validates their structure.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


@dataclass
class KnowledgeBaseConfig:
    """Knowledge base configuration for an agent."""
    enabled: bool = False
    collection: str = ""
    top_k: int = 5
    similarity_threshold: float = 0.7
    vector_db_type: str = "qdrant"
    vector_db_config: Dict[str, Any] = field(default_factory=dict)
    document_paths: List[str] = field(default_factory=list)
    file_storage_type: str = "local"
    file_storage_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorConfig:
    """Behavior configuration for an agent."""
    temperature: float = 0.3
    max_tokens: int = 2000
    response_style: str = "professional"
    tone: str = "professional"


@dataclass
class AgentPolicy:
    """Agent policy definition."""
    version: str = "1.0.0"
    name: str = ""
    display_name: str = ""
    description: str = ""
    personality: str = ""
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)
    capabilities: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyLoader:
    """Loads and validates agent policies from YAML files."""
    
    def __init__(self, policies_path: str = "/app/policies/agents"):
        self.policies_path = Path(policies_path)
        self.logger = get_logger()
        self._policies: Dict[str, AgentPolicy] = {}
        self._load_policies()
    
    def _load_policies(self):
        """Load all policy files from the policies directory."""
        if not self.policies_path.exists():
            self.logger.warn("Policies directory not found", path=str(self.policies_path))
            return
        
        for policy_file in self.policies_path.glob("*.yaml"):
            try:
                policy = self._load_policy_file(policy_file)
                if policy:
                    self._policies[policy.name] = policy
                    self.logger.info("Policy loaded", agent=policy.name, file=str(policy_file))
            except Exception as e:
                self.logger.error("Failed to load policy", error=str(e), file=str(policy_file))
    
    def _load_policy_file(self, policy_file: Path) -> Optional[AgentPolicy]:
        """Load and validate a single policy file."""
        with open(policy_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data or "agent" not in data:
            raise ValueError("Invalid policy structure: missing 'agent' key")
        
        agent_data = data["agent"]
        
        # Validate required fields
        if "name" not in agent_data:
            raise ValueError("Invalid policy: missing 'name'")
        
        # Build policy object
        policy = AgentPolicy(
            version=data.get("version", "1.0.0"),
            name=agent_data["name"],
            display_name=agent_data.get("display_name", agent_data["name"].title()),
            description=agent_data.get("description", ""),
            personality=agent_data.get("personality", ""),
        )
        
        # Load knowledge base config
        if "knowledge_base" in agent_data:
            kb_data = agent_data["knowledge_base"]
            policy.knowledge_base = KnowledgeBaseConfig(
                enabled=kb_data.get("enabled", False),
                collection=kb_data.get("vector_db", {}).get("collection", f"{policy.name}_kb"),
                top_k=kb_data.get("vector_db", {}).get("top_k", 5),
                similarity_threshold=kb_data.get("vector_db", {}).get("similarity_threshold", 0.7),
                vector_db_type=kb_data.get("vector_db", {}).get("type", "qdrant"),
                vector_db_config=kb_data.get("vector_db", {}).get("config", {}),
                document_paths=kb_data.get("documents", {}).get("paths", []),
                file_storage_type=kb_data.get("documents", {}).get("type", "local"),
                file_storage_config=kb_data.get("documents", {}).get("config", {}),
            )
        
        # Load behavior config
        if "behavior" in agent_data:
            behavior_data = agent_data["behavior"]
            policy.behavior = BehaviorConfig(
                temperature=behavior_data.get("temperature", 0.3),
                max_tokens=behavior_data.get("max_tokens", 2000),
                response_style=behavior_data.get("response_style", "professional"),
                tone=behavior_data.get("tone", "professional"),
            )
        
        # Load capabilities and constraints
        policy.capabilities = agent_data.get("capabilities", [])
        policy.constraints = agent_data.get("constraints", [])
        policy.metadata = agent_data.get("metadata", {})
        
        return policy
    
    def get_policy(self, agent_name: str) -> Optional[AgentPolicy]:
        """Get policy for an agent."""
        return self._policies.get(agent_name.lower())
    
    def list_agents(self) -> List[str]:
        """List all available agent names."""
        return sorted(self._policies.keys())
    
    def reload(self):
        """Reload all policies (for hot reload)."""
        self._policies.clear()
        self._load_policies()
        self.logger.info("Policies reloaded")


# Global policy loader instance
_policy_loader: Optional[PolicyLoader] = None


def get_policy_loader() -> PolicyLoader:
    """Get or create policy loader instance."""
    global _policy_loader
    
    if _policy_loader is None:
        policies_path = os.getenv("AGENT_POLICIES_PATH", "/app/policies/agents")
        _policy_loader = PolicyLoader(policies_path=policies_path)
    
    return _policy_loader

