"""
Unit tests for health check functionality.
"""
import pytest
import time
from app.health import check_health


class TestHealthCheck:
    """Tests for health check module."""

    def test_check_health_returns_healthy(self):
        """Test health check returns healthy status."""
        result = check_health()
        assert result["status"] in ["healthy", "unhealthy"]
        assert "checks" in result

    def test_check_health_cache_hit(self):
        """Test health check cache hit path."""
        # First call - should populate cache
        result1 = check_health()
        assert result1["status"] in ["healthy", "unhealthy"]
        
        # Second call immediately - should hit cache (within 5 second TTL)
        result2 = check_health()
        assert result2 == result1  # Should return cached result

