"""
Contract testing with Pact for AI Service.

Contract tests verify that the service API matches the expected contract
defined by consumers.
"""

import pytest
import json
from pact import Consumer, Provider, Like, EachLike
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def pact():
    """Pact test fixture."""
    return Consumer('server').has_pact_with(Provider('ai-service'))


class TestChatEndpointContract:
    """Contract tests for chat endpoint."""
    
    def test_chat_endpoint_contract(self, pact, client):
        """Test chat endpoint matches expected contract."""
        expected_response = {
            "agent": Like("startup"),
            "output": Like("This is a test response")
        }
        
        # Define expected interaction
        (pact
         .given('agent startup exists')
         .upon_receiving('a chat request')
         .with_request(
             method='POST',
             path='/v1/chat',
             headers={'Content-Type': 'application/json'},
             body={
                 "agent": "startup",
                 "input": "What is a startup?"
             }
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))
        
        # Verify contract
        with pact:
            response = client.post(
                "/v1/chat",
                json={"agent": "startup", "input": "What is a startup?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "agent" in data
            assert "output" in data


class TestAgentsEndpointContract:
    """Contract tests for agents list endpoint."""
    
    def test_agents_endpoint_contract(self, pact, client):
        """Test agents endpoint matches expected contract."""
        expected_response = EachLike("startup")
        
        (pact
         .given('agents are available')
         .upon_receiving('a request for agents list')
         .with_request(
             method='GET',
             path='/v1/agents'
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))
        
        with pact:
            response = client.get("/v1/agents")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0


class TestHealthEndpointContract:
    """Contract tests for health endpoint."""
    
    def test_health_endpoint_contract(self, pact, client):
        """Test health endpoint matches expected contract."""
        expected_response = {
            "status": Like("healthy"),
            "service": Like("ai-service"),
            "checks": EachLike({
                "name": Like("service"),
                "status": Like("ok")
            })
        }
        
        (pact
         .given('service is healthy')
         .upon_receiving('a health check request')
         .with_request(
             method='GET',
             path='/healthz'
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))
        
        with pact:
            response = client.get("/healthz")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert "checks" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

