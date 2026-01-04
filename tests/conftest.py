"""
Pytest configuration and shared fixtures.
"""
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_chat_model():
    """Mock LangChain chat model."""
    model = Mock(spec=BaseChatModel)
    model.ainvoke = AsyncMock(return_value=AIMessage(content="Mock response"))
    model.astream_events = AsyncMock()
    return model


@pytest.fixture
def mock_cipher_client():
    """Mock CipherClient."""
    client = Mock()
    client.chat = AsyncMock(return_value="Mock cipher response")
    client.generate_images = AsyncMock(return_value=[
        {"url": "https://example.com/image.png"}
    ])
    return client


@pytest.fixture
def sample_chat_request():
    """Sample chat request data."""
    return {
        "agent": "startup",
        "input": "What is a good MVP strategy?",
        "provider": "openai"
    }


@pytest.fixture
def sample_image_request():
    """Sample image generation request data."""
    return {
        "provider": "cipher",
        "prompt": "A futuristic cityscape",
        "n": 1,
        "size": "1024x1024"
    }


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables before each test."""
    # Store original values
    original_env = os.environ.copy()
    yield
    # Restore original values
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def mock_agent_policies():
    """Mock agent policies for all tests."""
    from app.agents.policy import AgentPolicy, KnowledgeBaseConfig, BehaviorConfig
    
    policies = {
        "startup": AgentPolicy(
            version="1.0.0",
            name="startup",
            display_name="Startup Advisor Agent",
            description="A startup advisor and mentor",
            personality="A startup advisor and mentor. Blend product thinking, growth, fundraising, and execution advice tailored to stage.",
            knowledge_base=KnowledgeBaseConfig(enabled=False),
            behavior=BehaviorConfig(temperature=0.3, max_tokens=2000),
        ),
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
    
    with patch('app.agents.registry.get_policy_loader') as mock_get_loader, \
         patch('app.main.get_agent_names') as mock_get_names, \
         patch('app.agents.get_agent_names') as mock_get_names_module:
        loader = Mock()
        agent_list = sorted(policies.keys())
        loader.list_agents.return_value = agent_list
        loader.get_policy = lambda name: policies.get(name.lower())
        mock_get_loader.return_value = loader
        mock_get_names.return_value = agent_list
        mock_get_names_module.return_value = agent_list
        yield