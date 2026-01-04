"""
Unit tests for agent registry and agent building.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable

from app.agents import (
    get_agent_names,
    get_agent,
    build_agent_with_model,
    build_system_message
)
from app.agents.policy import AgentPolicy, KnowledgeBaseConfig, BehaviorConfig


@pytest.fixture
def mock_agent_policy():
    """Create a mock agent policy."""
    return AgentPolicy(
        version="1.0.0",
        name="startup",
        display_name="Startup Advisor Agent",
        description="A startup advisor and mentor",
        personality="A startup advisor and mentor. Blend product thinking, growth, fundraising, and execution advice tailored to stage.",
        knowledge_base=KnowledgeBaseConfig(enabled=False),
        behavior=BehaviorConfig(temperature=0.3, max_tokens=2000),
        capabilities=["product_thinking", "growth"],
        constraints=[],
        metadata={}
    )


@pytest.fixture
def mock_policy_loader(mock_agent_policy):
    """Mock policy loader with test policies."""
    policies = {
        "startup": mock_agent_policy,
        "economist": AgentPolicy(
            version="1.0.0",
            name="economist",
            display_name="Economist Agent",
            description="An economist advisor",
            personality="An economist advisor providing economic insights.",
            knowledge_base=KnowledgeBaseConfig(enabled=False),
            behavior=BehaviorConfig(temperature=0.3),
        ),
        "strategist": AgentPolicy(
            version="1.0.0",
            name="strategist",
            display_name="Strategist Agent",
            description="A strategist advisor",
            personality="A strategist advisor providing strategic insights.",
            knowledge_base=KnowledgeBaseConfig(enabled=False),
            behavior=BehaviorConfig(temperature=0.3),
        ),
        "entrepreneur": AgentPolicy(
            version="1.0.0",
            name="entrepreneur",
            display_name="Entrepreneur Agent",
            description="An entrepreneur advisor",
            personality="An entrepreneur advisor providing business insights.",
            knowledge_base=KnowledgeBaseConfig(enabled=False),
            behavior=BehaviorConfig(temperature=0.3),
        ),
    }
    
    loader = Mock()
    loader.list_agents.return_value = sorted(policies.keys())
    loader.get_policy = lambda name: policies.get(name.lower())
    
    return loader


class TestAgentRegistry:
    """Tests for agent registry functions."""

    @patch('app.agents.registry.get_policy_loader')
    def test_get_agent_names(self, mock_get_loader, mock_policy_loader):
        """Test getting list of available agent names."""
        mock_get_loader.return_value = mock_policy_loader
        names = get_agent_names()
        assert isinstance(names, list)
        assert len(names) > 0
        assert "economist" in names
        assert "strategist" in names
        assert "entrepreneur" in names
        assert "startup" in names
        # Should be sorted
        assert names == sorted(names)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('langchain_openai.ChatOpenAI')
    @patch('app.agents.registry.get_policy_loader')
    def test_get_agent_valid_name(self, mock_get_loader, mock_chat_openai, mock_policy_loader, mock_chat_model):
        """Test getting an agent with a valid name."""
        mock_get_loader.return_value = mock_policy_loader
        mock_chat_openai.return_value = mock_chat_model
        agent = get_agent("startup")
        assert agent is not None
        assert isinstance(agent, Runnable)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('langchain_openai.ChatOpenAI')
    @patch('app.agents.registry.get_policy_loader')
    def test_get_agent_case_insensitive(self, mock_get_loader, mock_chat_openai, mock_policy_loader, mock_chat_model):
        """Test that agent names are case-insensitive."""
        mock_get_loader.return_value = mock_policy_loader
        mock_chat_openai.return_value = mock_chat_model
        agent1 = get_agent("STARTUP")
        agent2 = get_agent("startup")
        agent3 = get_agent("Startup")
        assert agent1 is not None
        assert agent2 is not None
        assert agent3 is not None

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('langchain_openai.ChatOpenAI')
    @patch('app.agents.registry.get_policy_loader')
    def test_get_agent_with_whitespace(self, mock_get_loader, mock_chat_openai, mock_policy_loader, mock_chat_model):
        """Test that agent names are trimmed."""
        mock_get_loader.return_value = mock_policy_loader
        mock_chat_openai.return_value = mock_chat_model
        agent = get_agent("  startup  ")
        assert agent is not None

    @patch('app.agents.registry.get_policy_loader')
    def test_get_agent_invalid_name(self, mock_get_loader, mock_policy_loader):
        """Test getting an agent with an invalid name."""
        mock_get_loader.return_value = mock_policy_loader
        agent = get_agent("nonexistent")
        assert agent is None

    @pytest.mark.parametrize("agent_name", ["economist", "strategist", "entrepreneur", "startup"])
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('langchain_openai.ChatOpenAI')
    @patch('app.agents.registry.get_policy_loader')
    def test_get_agent_all_agents(self, mock_get_loader, mock_chat_openai, agent_name, mock_policy_loader, mock_chat_model):
        """Test that all defined agents can be retrieved."""
        mock_get_loader.return_value = mock_policy_loader
        mock_chat_openai.return_value = mock_chat_model
        agent = get_agent(agent_name)
        assert agent is not None
        assert isinstance(agent, Runnable)


class TestBuildAgentWithModel:
    """Tests for building agents with custom models."""

    @patch('app.agents.registry.get_policy_loader')
    def test_build_agent_with_model_valid(self, mock_get_loader, mock_chat_model, mock_policy_loader):
        """Test building an agent with a valid model."""
        mock_get_loader.return_value = mock_policy_loader
        agent = build_agent_with_model("startup", mock_chat_model)
        assert agent is not None
        assert isinstance(agent, Runnable)

    @patch('app.agents.registry.get_policy_loader')
    def test_build_agent_with_model_invalid_name(self, mock_get_loader, mock_chat_model, mock_policy_loader):
        """Test building an agent with invalid name."""
        mock_get_loader.return_value = mock_policy_loader
        agent = build_agent_with_model("nonexistent", mock_chat_model)
        assert agent is None

    @patch('app.agents.registry.get_policy_loader')
    def test_build_agent_with_model_case_insensitive(self, mock_get_loader, mock_chat_model, mock_policy_loader):
        """Test that agent names are case-insensitive."""
        mock_get_loader.return_value = mock_policy_loader
        agent1 = build_agent_with_model("STARTUP", mock_chat_model)
        agent2 = build_agent_with_model("startup", mock_chat_model)
        assert agent1 is not None
        assert agent2 is not None

    @pytest.mark.parametrize("agent_name", ["economist", "strategist", "entrepreneur", "startup"])
    @patch('app.agents.registry.get_policy_loader')
    def test_build_agent_with_model_all_agents(self, mock_get_loader, agent_name, mock_chat_model, mock_policy_loader):
        """Test building all agents with custom model."""
        mock_get_loader.return_value = mock_policy_loader
        agent = build_agent_with_model(agent_name, mock_chat_model)
        assert agent is not None
        assert isinstance(agent, Runnable)


class TestBuildSystemMessage:
    """Tests for building system messages."""

    @patch('app.agents.registry.get_policy_loader')
    def test_build_system_message_valid(self, mock_get_loader, mock_policy_loader):
        """Test building system message for valid agent."""
        mock_get_loader.return_value = mock_policy_loader
        message = build_system_message("startup")
        assert message is not None
        assert isinstance(message, str)
        assert "Startup" in message or "startup" in message.lower()
        assert len(message) > 0

    @patch('app.agents.registry.get_policy_loader')
    def test_build_system_message_invalid(self, mock_get_loader, mock_policy_loader):
        """Test building system message for invalid agent."""
        mock_get_loader.return_value = mock_policy_loader
        message = build_system_message("nonexistent")
        assert message is None

    @patch('app.agents.registry.get_policy_loader')
    def test_build_system_message_case_insensitive(self, mock_get_loader, mock_policy_loader):
        """Test that agent names are case-insensitive."""
        mock_get_loader.return_value = mock_policy_loader
        msg1 = build_system_message("STARTUP")
        msg2 = build_system_message("startup")
        assert msg1 is not None
        assert msg2 is not None
        assert msg1 == msg2

    @pytest.mark.parametrize("agent_name", ["economist", "strategist", "entrepreneur", "startup"])
    @patch('app.agents.registry.get_policy_loader')
    def test_build_system_message_all_agents(self, mock_get_loader, agent_name, mock_policy_loader):
        """Test building system messages for all agents."""
        mock_get_loader.return_value = mock_policy_loader
        message = build_system_message(agent_name)
        assert message is not None
        assert isinstance(message, str)
        assert agent_name.title() in message or agent_name.lower() in message.lower()

    @patch('app.agents.registry.get_policy_loader')
    def test_build_system_message_contains_persona(self, mock_get_loader, mock_policy_loader):
        """Test that system message contains persona description."""
        mock_get_loader.return_value = mock_policy_loader
        message = build_system_message("startup")
        assert "startup" in message.lower() or "advisor" in message.lower() or "mentor" in message.lower()
