"""
Circuit Breaker pattern implementation for fault tolerance.
Prevents requests to repeatedly failing services.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from loguru import logger

from evcharging.common.utils import utc_now


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests due to failures
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying HALF_OPEN state
            half_open_max_calls: Number of test calls allowed in HALF_OPEN state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.half_open_calls = 0
    
    def call_succeeded(self):
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self.half_open_calls += 1
            
            # If we have enough successes in HALF_OPEN, close the circuit
            if self.success_count >= self.half_open_max_calls:
                self._close_circuit()
                logger.info("Circuit breaker: Service recovered, circuit CLOSED")
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def call_failed(self):
        """Record a failed call."""
        self.last_failure_time = utc_now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN immediately opens circuit again
            self._open_circuit()
            logger.warning("Circuit breaker: Failure during recovery test, circuit OPEN")
        
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            
            # Check if we should open the circuit
            if self.failure_count >= self.failure_threshold:
                self._open_circuit()
                logger.error(
                    f"Circuit breaker: Failure threshold ({self.failure_threshold}) "
                    f"reached, circuit OPEN"
                )
    
    def is_call_allowed(self) -> bool:
        """Check if a call is currently allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if enough time has passed to try recovery
            if self._should_attempt_recovery():
                self._half_open_circuit()
                logger.info("Circuit breaker: Attempting recovery, circuit HALF_OPEN")
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited calls in HALF_OPEN state
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def reset(self):
        """Manually reset the circuit breaker."""
        self._close_circuit()
        logger.info("Circuit breaker: Manually reset to CLOSED")
    
    def _open_circuit(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = utc_now()
        self.half_open_calls = 0
    
    def _half_open_circuit(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
    
    def _close_circuit(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.opened_at = None
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if not self.opened_at:
            return True
        
        elapsed = (utc_now() - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
        }
