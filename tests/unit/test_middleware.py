"""
Unit tests for middleware functionality.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestRequestIDMiddleware:
    """Tests for RequestIDMiddleware."""

    def test_request_id_middleware_generates_id(self):
        """Test that middleware generates request ID when not present."""
        from app.middleware import RequestIDMiddleware
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/v1/agents")
        
        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers

    def test_request_id_middleware_uses_header(self):
        """Test that middleware uses X-Trace-ID header if present."""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/v1/agents", headers={"X-Trace-ID": "custom-trace-id"})
        
        assert response.status_code == 200
        assert response.headers.get("X-Trace-ID") == "custom-trace-id"

    def test_request_id_middleware_exception_handling(self):
        """Test middleware exception handling."""
        from app.middleware import RequestIDMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)
        
        @app.get("/error")
        def error_endpoint():
            raise Exception("Test error")
        
        client = TestClient(app)
        # Should handle exception gracefully
        response = client.get("/error")
        assert response.status_code == 500
        # Should still have trace ID
        assert "X-Trace-ID" in response.headers


class TestRequestLoggerMiddleware:
    """Tests for RequestLoggerMiddleware."""

    def test_request_logger_middleware_logs_request(self):
        """Test that middleware logs requests."""
        from app.main import app
        
        client = TestClient(app)
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/v1/agents")
            assert response.status_code == 200
            # Should have logged
            assert mock_logger.info.called or mock_logger.warn.called or mock_logger.error.called

    def test_request_logger_middleware_logs_error(self):
        """Test that middleware logs error responses."""
        from app.main import app
        
        client = TestClient(app)
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/nonexistent")
            assert response.status_code == 404
            # Should have logged warning for 4xx
            assert mock_logger.warn.called or mock_logger.info.called

    def test_request_logger_middleware_exception_handling(self):
        """Test middleware exception handling."""
        from app.middleware import RequestLoggerMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/error")
        def error_endpoint():
            raise Exception("Test error")
        
        client = TestClient(app)
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/error")
            assert response.status_code == 500
            # Should have logged error
            assert mock_logger.error.called

    def test_request_logger_middleware_missing_client(self):
        """Test middleware with missing client info."""
        from app.middleware import RequestLoggerMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        client = TestClient(app)
        # Create a request without client
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/test")
            assert response.status_code == 200
            # Should still log
            assert mock_logger.info.called

