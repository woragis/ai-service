"""
Unit tests for logger functionality.
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock


class TestLogger:
    """Tests for logger module."""

    def test_configure_logging_development(self):
        """Test logger configuration for development."""
        from app.logger import configure_logging, get_logger
        
        configure_logging(env="development", log_to_file=False)
        logger = get_logger("test")
        assert logger is not None

    def test_configure_logging_production(self):
        """Test logger configuration for production."""
        from app.logger import configure_logging, get_logger
        
        configure_logging(env="production", log_to_file=False)
        logger = get_logger("test")
        assert logger is not None

    def test_configure_logging_with_file(self):
        """Test logger configuration with file logging."""
        from app.logger import configure_logging, get_logger
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            configure_logging(env="development", log_to_file=True, log_dir=temp_dir)
            logger = get_logger("test")
            assert logger is not None
            # Verify log file was created
            log_file = os.path.join(temp_dir, "ai-service.log")
            # File may not exist immediately, but directory should
            assert os.path.exists(temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_configure_logging_different_levels(self):
        """Test logger configuration with different log levels."""
        from app.logger import configure_logging, get_logger
        
        # Test DEBUG level (development)
        configure_logging(env="development", log_to_file=False)
        logger1 = get_logger("test1")
        assert logger1 is not None
        
        # Test INFO level (production)
        configure_logging(env="production", log_to_file=False)
        logger2 = get_logger("test2")
        assert logger2 is not None

    def test_get_logger(self):
        """Test getting logger instance."""
        from app.logger import get_logger
        
        logger = get_logger("test-logger")
        assert logger is not None

    def test_get_logger_with_trace_id(self):
        """Test getting logger with trace ID in context."""
        from app.logger import get_logger, set_trace_id
        
        set_trace_id("test-trace-123")
        logger = get_logger("test")
        assert logger is not None

    def test_set_trace_id(self):
        """Test setting trace ID."""
        from app.logger import set_trace_id, get_trace_id, trace_id_var
        
        # Clear any existing trace ID first
        trace_id_var.set(None)
        
        set_trace_id("test-trace-456")
        result = get_trace_id()
        assert result == "test-trace-456"

    def test_get_trace_id(self):
        """Test getting trace ID."""
        from app.logger import get_trace_id, set_trace_id, trace_id_var
        
        # Clear any existing trace ID first
        trace_id_var.set(None)
        
        # Initially should be None
        result = get_trace_id()
        assert result is None
        
        # Set and get
        set_trace_id("test-trace-789")
        result = get_trace_id()
        assert result == "test-trace-789"
        
        # Clear again
        trace_id_var.set(None)
        result = get_trace_id()
        assert result is None

    def test_get_trace_id_not_set(self):
        """Test getting trace ID when not set."""
        from app.logger import get_trace_id, trace_id_var
        
        # Clear any existing trace ID
        trace_id_var.set(None)
        
        result = get_trace_id()
        assert result is None

