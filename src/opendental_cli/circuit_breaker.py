"""Circuit Breaker Pattern Implementation.

Prevents cascading failures by opening circuit after consecutive failures.
Per-endpoint state tracking for fine-grained control.

Article III Compliance: Circuit Breaker Pattern
"""

import time
from enum import Enum
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """Circuit breaker for endpoint resilience.

    Opens after failure_threshold consecutive failures.
    Stays open for cooldown_seconds before allowing probe.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: int = 60,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening (default: 5)
            cooldown_seconds: Cooldown before half-open (default: 60)
        """
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: float | None = None

    def call(self, func: Callable[[], T]) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from func
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit open, cooldown until {self._cooldown_end_time()}"
                )

        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if cooldown period has elapsed."""
        if self.last_failure_time is None:
            return True
        return time.time() >= self.last_failure_time + self.cooldown_seconds

    def _cooldown_end_time(self) -> str:
        """Get cooldown end time as ISO string."""
        if self.last_failure_time is None:
            return "unknown"
        end_time = self.last_failure_time + self.cooldown_seconds
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time))


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass
