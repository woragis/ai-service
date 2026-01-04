"""
Unit tests for API endpoints.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestListAgents:
    """Tests for GET /v1/agents endpoint."""

    @patch('app.main.get_agent_names')
    def test_list_agents(self, mock_get_names, client):
        """Test listing available agents."""
        mock_get_names.return_value = ["economist", "entrepreneur", "startup", "strategist"]
        response = client.get("/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "economist" in data
        assert "strategist" in data
        assert "entrepreneur" in data
        assert "startup" in data


class TestHealthCheck:
    """Tests for GET /healthz endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    def test_health_check_unhealthy(self, client):
        """Test health check endpoint returns unhealthy status."""
        with patch('app.health.check_health') as mock_health:
            mock_health.return_value = {
                "status": "unhealthy",
                "checks": [{"name": "service", "status": "error"}]
            }
            response = client.get("/healthz")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"


class TestPickAgentAuto:
    """Tests for automatic agent selection logic via API."""

    @patch('app.main.execute_with_fallback')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.is_rag_enabled')
    def test_pick_agent_economist(self, mock_rag, mock_pii, mock_content, mock_injection, mock_execute, client):
        """Test picking economist agent via auto selection."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_rag.return_value = False
        mock_execute.return_value = Mock(content="Response")
        
        request_data = {
            "agent": "auto",
            "input": "What are the market trends and inflation rates?",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "economist"

    @patch('app.main.execute_with_fallback')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.is_rag_enabled')
    def test_pick_agent_strategist(self, mock_rag, mock_pii, mock_content, mock_injection, mock_execute, client):
        """Test picking strategist agent via auto selection (not economist)."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_rag.return_value = False
        mock_execute.return_value = Mock(content="Response")
        
        request_data = {
            "agent": "auto",
            "input": "What is our competitive positioning and strategy?",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        data = response.json()
        # Should pick strategist (strategy keyword triggers it)
        assert data["agent"] == "strategist"

    @patch('app.main.execute_with_fallback')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.is_rag_enabled')
    def test_pick_agent_entrepreneur(self, mock_rag, mock_pii, mock_content, mock_injection, mock_execute, client):
        """Test picking entrepreneur agent via auto selection."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_rag.return_value = False
        mock_execute.return_value = Mock(content="Response")
        
        request_data = {
            "agent": "auto",
            "input": "How do I build an MVP and validate my idea quickly?",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "entrepreneur"

    @patch('app.main.execute_with_fallback')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.is_rag_enabled')
    def test_pick_agent_startup_default(self, mock_rag, mock_pii, mock_content, mock_injection, mock_execute, client):
        """Test default to startup agent via auto selection."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_rag.return_value = False
        mock_execute.return_value = Mock(content="Response")
        
        request_data = {
            "agent": "auto",
            "input": "General startup question",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "startup"


class TestChatEndpoint:
    """Tests for POST /v1/chat endpoint."""

    @patch('app.main.execute_with_fallback')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.is_rag_enabled')
    def test_chat_success(self, mock_rag, mock_pii, mock_content, mock_injection, mock_execute, client):
        """Test successful chat request."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_rag.return_value = False
        mock_execute.return_value = Mock(content="Test response")
        
        request_data = {
            "agent": "startup",
            "input": "What is a good MVP strategy?",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert "output" in data
        assert data["agent"] == "startup"
        assert data["output"] == "Test response"

    def test_chat_invalid_agent(self, client, mock_chat_model):
        """Test chat with invalid agent name."""
        request_data = {
            "agent": "nonexistent",
            "input": "Hello",
            "provider": "openai"
        }
        
        with patch('app.main.make_model') as mock_make, \
             patch('app.main.build_agent_with_model', return_value=None), \
             patch('app.main.get_logger'):
            mock_make.return_value = mock_chat_model
            response = client.post("/v1/chat", json=request_data)
            # FastAPI validates the request first, so invalid enum values return 422
            # But if the agent is valid enum but not found, it returns 404
            assert response.status_code in [404, 422]

    @patch('app.main.execute_with_fallback')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.is_rag_enabled')
    def test_chat_auto_agent(self, mock_rag, mock_pii, mock_content, mock_injection, mock_execute, client):
        """Test chat with auto agent selection."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_rag.return_value = False
        mock_execute.return_value = Mock(content="Response")
        
        request_data = {
            "agent": "auto",
            "input": "What are the market trends?",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        # Should have selected economist based on keywords
        data = response.json()
        assert data["agent"] == "economist"

    @patch('app.main.CipherClient')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.build_system_message')
    def test_chat_cipher_provider(self, mock_build_system, mock_pii, mock_content, mock_injection, mock_cipher_class, client):
        """Test chat with Cipher provider."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_build_system.return_value = "You are a startup advisor."
        mock_client = Mock()
        mock_client.chat = AsyncMock(return_value="Cipher response")
        mock_cipher_class.from_env.return_value = mock_client
        
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "cipher"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "Cipher response"

    def test_chat_cipher_provider_invalid_agent(self, client):
        """Test cipher provider with invalid agent (when build_system_message returns None)."""
        # Mock build_system_message to return None to trigger the 404 path
        with patch('app.main.CipherClient') as mock_cipher_class, \
             patch('app.main.build_system_message', return_value=None), \
             patch('app.main.get_agent_names', return_value=["startup", "economist"]):
            request_data = {
                "agent": "startup",  # Valid enum, but build_system_message returns None
                "input": "Hello",
                "provider": "cipher"
            }
            response = client.post("/v1/chat", json=request_data)
            assert response.status_code == 404
            assert "Unknown agent" in response.json()["detail"]

    @patch('app.main.CipherClient')
    def test_chat_cipher_provider_with_system(self, mock_cipher_class, client):
        """Test cipher provider with system message."""
        mock_client = Mock()
        mock_client.chat = AsyncMock(return_value="Cipher response")
        mock_cipher_class.from_env.return_value = mock_client
        
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "system": "Be concise",
            "provider": "cipher"
        }
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        # Verify system message was added
        assert mock_client.chat.called
        # Check that system message was in the call (chat is called with keyword args)
        call_kwargs = mock_client.chat.call_args.kwargs
        messages = call_kwargs.get('messages', [])
        assert any(msg.get("role") == "system" and "Be concise" in msg.get("content", "") for msg in messages)

    @patch('app.main.execute_with_fallback')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.is_rag_enabled')
    def test_chat_with_system_message(self, mock_rag, mock_pii, mock_content, mock_injection, mock_execute, client):
        """Test chat with additional system message."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_rag.return_value = False
        mock_execute.return_value = Mock(content="Response")
        
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "system": "Be very concise",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200

    def test_chat_invalid_provider(self, client):
        """Test chat with invalid provider."""
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "invalid"
        }
        
        # FastAPI validates enum values, so invalid provider returns 422
        with patch('app.main.get_logger'):
            response = client.post("/v1/chat", json=request_data)
            assert response.status_code == 422  # Validation error for invalid enum


class TestImageGeneration:
    """Tests for POST /v1/images endpoint."""

    @patch('app.main.CipherClient')
    def test_generate_images_success(self, mock_cipher_class, client):
        """Test successful image generation."""
        mock_client = Mock()
        mock_client.generate_images = AsyncMock(return_value=[
            {"url": "https://example.com/image.png"}
        ])
        mock_cipher_class.from_env.return_value = mock_client
        
        request_data = {
            "provider": "cipher",
            "prompt": "A futuristic cityscape",
            "n": 1,
            "size": "1024x1024"
        }
        
        response = client.post("/v1/images", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert "url" in data["data"][0] or "b64_json" in data["data"][0]

    def test_generate_images_invalid_provider(self, client):
        """Test image generation with invalid provider."""
        request_data = {
            "provider": "openai",
            "prompt": "A test image"
        }
        
        # FastAPI validates enum values, so invalid provider returns 422
        with patch('app.main.get_logger'):
            response = client.post("/v1/images", json=request_data)
            # The endpoint checks provider == "cipher" and returns 400, but FastAPI validates enum first
            # So we check for either 400 (if validation passes) or 422 (if enum validation fails)
            assert response.status_code in [400, 422]


class TestChatStream:
    """Tests for POST /v1/chat/stream endpoint."""

    @patch('app.main.make_model')
    @patch('app.main.build_agent_with_model')
    def test_chat_stream_success(self, mock_build_agent, mock_make_model, client, mock_chat_model):
        """Test successful streaming chat."""
        mock_make_model.return_value = mock_chat_model
        mock_chain = Mock()
        
        # Mock streaming events
        async def mock_stream():
            yield {"event": "on_llm_new_token", "data": {"chunk": Mock(content="Hello")}}
            yield {"event": "on_llm_new_token", "data": {"chunk": Mock(content=" World")}}
        
        mock_chain.astream_events = AsyncMock(return_value=mock_stream())
        mock_build_agent.return_value = mock_chain
        
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat/stream", json=request_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-ndjson"

    @patch('app.main.CipherClient')
    @patch('app.main.build_system_message')
    def test_chat_stream_cipher(self, mock_build_system, mock_cipher_class, client):
        """Test streaming with Cipher provider."""
        mock_build_system.return_value = "You are a startup advisor."
        mock_client = Mock()
        mock_client.chat = AsyncMock(return_value="Full response")
        mock_cipher_class.from_env.return_value = mock_client
        
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "cipher"
        }
        
        response = client.post("/v1/chat/stream", json=request_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-ndjson"

    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    def test_chat_model_creation_error(self, mock_pii, mock_content, mock_injection, client):
        """Test chat endpoint with model creation error."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "openai"
        }
        
        with patch('app.main.make_model') as mock_make:
            mock_make.side_effect = ValueError("Invalid model")
            response = client.post("/v1/chat", json=request_data)
            assert response.status_code == 400
            assert "Invalid model" in response.json()["detail"]

    def test_chat_invalid_agent_404(self, client, mock_chat_model):
        """Test chat with invalid agent returns 404."""
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "openai"
        }
        
        with patch('app.main.make_model') as mock_make, \
             patch('app.main.build_agent_with_model', return_value=None), \
             patch('app.main.get_agent_names', return_value=["economist", "startup"]), \
             patch('app.main.get_logger'):
            mock_make.return_value = mock_chat_model
            response = client.post("/v1/chat", json=request_data)
            assert response.status_code == 404

    @patch('app.main.execute_with_fallback')
    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    @patch('app.main.is_rag_enabled')
    def test_chat_result_extraction_string(self, mock_rag, mock_pii, mock_content, mock_injection, mock_execute, client):
        """Test chat result extraction when result is a string."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        mock_rag.return_value = False
        mock_execute.return_value = "String response"
        
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "openai"
        }
        
        response = client.post("/v1/chat", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "String response"

    @patch('app.main.check_prompt_injection')
    @patch('app.main.check_content_filter')
    @patch('app.main.check_pii')
    def test_stream_model_creation_error(self, mock_pii, mock_content, mock_injection, client):
        """Test streaming endpoint with model creation error."""
        mock_injection.return_value = (True, None)
        mock_content.return_value = (True, None)
        mock_pii.return_value = (True, None, {})
        
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "openai"
        }
        
        with patch('app.main.make_model') as mock_make:
            mock_make.side_effect = ValueError("Invalid model")
            response = client.post("/v1/chat/stream", json=request_data)
            assert response.status_code == 400

    def test_stream_invalid_agent(self, client, mock_chat_model):
        """Test streaming with invalid agent returns 404."""
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "openai"
        }
        
        with patch('app.main.make_model') as mock_make, \
             patch('app.main.build_agent_with_model', return_value=None), \
             patch('app.main.get_agent_names', return_value=["economist", "startup"]), \
             patch('app.main.get_logger'):
            mock_make.return_value = mock_chat_model
            response = client.post("/v1/chat/stream", json=request_data)
            assert response.status_code == 404

    def test_stream_exception_handling(self, client, mock_chat_model):
        """Test streaming exception handling."""
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "openai"
        }
        
        with patch('app.main.make_model') as mock_make, \
             patch('app.main.build_agent_with_model') as mock_build, \
             patch('app.main.get_logger'):
            mock_make.return_value = mock_chat_model
            mock_chain = Mock()
            
            # Mock stream that raises exception
            async def mock_stream_error():
                yield {"event": "on_llm_new_token", "data": {"chunk": Mock(content="Hello")}}
                raise Exception("Stream error")
            
            mock_chain.astream_events = AsyncMock(return_value=mock_stream_error())
            mock_build.return_value = mock_chain
            
            response = client.post("/v1/chat/stream", json=request_data)
            assert response.status_code == 200
            # Should handle exception gracefully

    def test_stream_with_system_message(self, client, mock_chat_model):
        """Test streaming with system message."""
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "system": "Be concise",
            "provider": "openai"
        }
        
        with patch('app.main.make_model') as mock_make, \
             patch('app.main.build_agent_with_model') as mock_build, \
             patch('app.main.get_logger'):
            mock_make.return_value = mock_chat_model
            mock_chain = Mock()
            
            async def mock_stream():
                yield {"event": "on_llm_new_token", "data": {"chunk": Mock(content="Hello")}}
            
            mock_chain.astream_events = AsyncMock(return_value=mock_stream())
            mock_build.return_value = mock_chain
            
            response = client.post("/v1/chat/stream", json=request_data)
            assert response.status_code == 200

    def test_apply_overrides_function(self):
        """Test _apply_overrides function."""
        from app.main import _apply_overrides
        from unittest.mock import Mock, patch
        import os
        
        mock_chain = Mock()
        
        # Test with no overrides - should return chain unchanged
        result = _apply_overrides(mock_chain, None, None)
        assert result == mock_chain
        
        # Test with model_name override
        with patch('langchain_openai.ChatOpenAI') as mock_chat, \
             patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4o-mini", "OPENAI_TEMPERATURE": "0.3"}):
            mock_model = Mock()
            mock_chat.return_value = mock_model
            result = _apply_overrides(mock_chain, "gpt-4", None)
            assert result is not None
            assert result == mock_model
            mock_chat.assert_called_once()
            # Verify it was called with correct parameters
            call_args = mock_chat.call_args
            assert call_args[1]['model'] == "gpt-4"
        
        # Test with temperature override
        with patch('langchain_openai.ChatOpenAI') as mock_chat, \
             patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4o-mini", "OPENAI_TEMPERATURE": "0.3"}):
            mock_model = Mock()
            mock_chat.return_value = mock_model
            result = _apply_overrides(mock_chain, None, 0.7)
            assert result is not None
            assert result == mock_model
            mock_chat.assert_called_once()
            # Verify temperature was set
            call_args = mock_chat.call_args
            assert call_args[1]['temperature'] == 0.7
        
        # Test with both overrides
        with patch('langchain_openai.ChatOpenAI') as mock_chat, \
             patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4o-mini", "OPENAI_TEMPERATURE": "0.3"}):
            mock_model = Mock()
            mock_chat.return_value = mock_model
            result = _apply_overrides(mock_chain, "gpt-4", 0.7)
            assert result is not None
            assert result == mock_model
            mock_chat.assert_called_once()
            # Verify both were set
            call_args = mock_chat.call_args
            assert call_args[1]['model'] == "gpt-4"
            assert call_args[1]['temperature'] == 0.7

    def test_stream_event_token_extraction(self, client, mock_chat_model):
        """Test streaming with token extraction from data."""
        request_data = {
            "agent": "startup",
            "input": "Hello",
            "provider": "openai"
        }
        
        with patch('app.main.make_model') as mock_make, \
             patch('app.main.build_agent_with_model') as mock_build, \
             patch('app.main.get_logger'):
            mock_make.return_value = mock_chat_model
            mock_chain = Mock()
            
            # Mock event with token instead of chunk
            async def mock_stream():
                yield {"event": "on_llm_new_token", "data": {"token": "Hello"}}
            
            mock_chain.astream_events = AsyncMock(return_value=mock_stream())
            mock_build.return_value = mock_chain
            
            response = client.post("/v1/chat/stream", json=request_data)
            assert response.status_code == 200