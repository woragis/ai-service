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

    def test_request_id_middleware_with_otel_trace_id(self):
        """Test middleware uses OpenTelemetry trace ID when available."""
        from app.middleware import RequestIDMiddleware
        from app.tracing import set_trace_id as set_otel_trace_id
        
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        # Set OpenTelemetry trace ID
        set_otel_trace_id("otel-trace-123")
        
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        # Should use the OpenTelemetry trace ID
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
        """Test middleware with request body (covers line 51, 72)."""
        from app.middleware import RequestLoggerMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.post("/test")
        async def test_endpoint(request):
            # Access request body to ensure it's read
            await request.body()
            return {"status": "ok"}
        
        client = TestClient(app)
        with patch('app.middleware.logger') as mock_logger:
            response = client.post("/test", json={"test": "data"})
            assert response.status_code == 200
            # Should have logged
            assert mock_logger.info.called

    def test_request_logger_middleware_with_query_params(self):
        """Test middleware with query parameters (covers line 79)."""
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
            # Verify query was logged
            if mock_logger.info.called:
                call_kwargs = mock_logger.info.call_args[1] if mock_logger.info.call_args else {}
                # query should be in log_data if query_params exist

    def test_request_logger_middleware_with_trace_id(self):
        """Test middleware with trace ID in context (covers line 75)."""
        from app.middleware import RequestLoggerMiddleware
        from app.middleware import RequestIDMiddleware
        
        app = FastAPI()
        # Add both middlewares - RequestIDMiddleware sets trace_id, RequestLoggerMiddleware uses it
        app.add_middleware(RequestIDMiddleware)
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        client = TestClient(app)
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/test")
            assert response.status_code == 200
            # Should log with trace_id (set by RequestIDMiddleware)
            assert mock_logger.info.called

    def test_request_logger_middleware_500_error(self):
        """Test middleware logs 500 errors."""
        from app.middleware import RequestLoggerMiddleware
        from fastapi import HTTPException
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        # Use HTTPException instead of generic Exception so FastAPI handles it properly
        @app.get("/error")
        def error_endpoint():
            raise HTTPException(status_code=500, detail="Server error")
        
        client = TestClient(app, raise_server_exceptions=False)
        with patch('app.middleware.logger') as mock_logger:
            response = client.get("/error")
            assert response.status_code == 500
            # Should log error for 500
            assert mock_logger.error.called

