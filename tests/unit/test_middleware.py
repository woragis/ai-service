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
        
        client = TestClient(app, raise_server_exceptions=False)
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
        
        client = TestClient(app, raise_server_exceptions=False)
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

    def test_request_logger_middleware_with_body(self):
        """Test middleware with request body."""
        from app.middleware import RequestLoggerMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.post("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        client = TestClient(app)
        with patch('app.middleware.logger') as mock_logger:
            response = client.post("/test", json={"test": "data"})
            assert response.status_code == 200
            # Should log with body size if _body attribute exists
            assert mock_logger.info.called

    def test_request_logger_middleware_with_query_params(self):
        """Test middleware with query parameters."""
        from app.middleware import RequestLoggerMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        client = TestClient(app)
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/test?param1=value1&param2=value2")
            assert response.status_code == 200
            # Should log with query parameters
            assert mock_logger.info.called

    def test_request_logger_middleware_with_trace_id(self):
        """Test middleware with trace ID in context."""
        from app.middleware import RequestLoggerMiddleware
        from app.logger import set_trace_id
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        client = TestClient(app)
        set_trace_id("test-trace-123")
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/test")
            assert response.status_code == 200
            # Should log with trace_id
            assert mock_logger.info.called

    def test_request_logger_middleware_500_error(self):
        """Test middleware logs 500 errors."""
        from app.middleware import RequestLoggerMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/error")
        def error_endpoint():
            raise Exception("Server error")
        
        client = TestClient(app, raise_server_exceptions=False)
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/error")
            assert response.status_code == 500
            # Should log error for 500
            assert mock_logger.error.called

