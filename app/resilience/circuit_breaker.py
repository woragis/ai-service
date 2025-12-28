"""
Circuit breaker implementation for provider resilience.
"""

import time
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass, field
from app.logger import get_logger

logger = get_logger()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for a provider."""
    provider: str
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    half_open_max_calls: int = 3
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0
    
    def record_success(self):
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker closing", provider=self.provider)
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call."""
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to open
            logger.warn("Circuit breaker reopening", provider=self.provider)
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                logger.warn("Circuit breaker opening", provider=self.provider, failures=self.failure_count)
                self.state = CircuitState.OPEN
    
    def can_attempt(self) -> bool:
        """Check if a call can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time) >= self.timeout:
                logger.info("Circuit breaker entering half-open", provider=self.provider)
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False


class CircuitBreakerManager:
    """Manages circuit breakers for all providers."""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.logger = get_logger()
    
    def get_breaker(self, provider: str, failure_threshold: int = 5, 
                   success_threshold: int = 2, timeout: float = 60.0,
                   half_open_max_calls: int = 3) -> CircuitBreaker:
        """Get or create circuit breaker for a provider."""
        if provider not in self.breakers:
            self.breakers[provider] = CircuitBreaker(
                provider=provider,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout=timeout,
                half_open_max_calls=half_open_max_calls,
            )
        return self.breakers[provider]
    
    def reset(self, provider: str):
        """Reset circuit breaker for a provider."""
        if provider in self.breakers:
            breaker = self.breakers[provider]
            breaker.state = CircuitState.CLOSED
            breaker.failure_count = 0
            breaker.success_count = 0
            breaker.half_open_calls = 0
            breaker.last_failure_time = None
            self.logger.info("Circuit breaker reset", provider=provider)


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get or create circuit breaker manager."""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager

