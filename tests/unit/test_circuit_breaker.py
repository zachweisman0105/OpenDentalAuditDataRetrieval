"""Unit Tests for Circuit Breaker Pattern.

Tests circuit breaker state transitions and failure threshold logic.
Verifies CLOSED → OPEN → HALF_OPEN → CLOSED flow.
"""

import time
from unittest.mock import Mock

import pytest

from opendental_cli.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


def test_circuit_opens_after_5_consecutive_failures():
    """Test circuit opens after reaching failure threshold.
    
    Contract: After 5 consecutive failures:
    1. Circuit state transitions from CLOSED to OPEN
    2. Subsequent calls raise CircuitBreakerOpenError
    3. Cooldown timer starts
    """
    breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=60)
    
    # Verify initial state is CLOSED
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    
    # Simulate 5 consecutive failures
    failing_func = Mock(side_effect=RuntimeError("API error"))
    
    for i in range(5):
        with pytest.raises(RuntimeError):
            breaker.call(failing_func)
        
        # Check failure count increments
        assert breaker.failure_count == i + 1
    
    # After 5 failures, circuit should be OPEN
    assert breaker.state == CircuitState.OPEN
    assert breaker.last_failure_time is not None
    
    # Subsequent calls should raise CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        breaker.call(failing_func)
    
    assert "Circuit open" in str(exc_info.value)
    assert "cooldown" in str(exc_info.value)


def test_circuit_half_open_probe_after_60s_cooldown():
    """Test circuit transitions to HALF_OPEN after cooldown period.
    
    Contract: After 60-second cooldown:
    1. Circuit allows one probe request (HALF_OPEN state)
    2. If probe succeeds, circuit closes
    3. If probe fails, circuit reopens with new cooldown
    """
    breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=1)  # 1s for faster test
    
    # Open the circuit with 5 failures
    failing_func = Mock(side_effect=RuntimeError("API error"))
    for _ in range(5):
        with pytest.raises(RuntimeError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Immediately trying again should raise CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        breaker.call(failing_func)
    
    # Wait for cooldown period
    time.sleep(1.1)  # Wait slightly longer than cooldown
    
    # Next call should transition to HALF_OPEN and execute
    # We'll test with a succeeding function to verify HALF_OPEN → CLOSED
    success_func = Mock(return_value="success")
    result = breaker.call(success_func)
    
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_closes_after_successful_probe():
    """Test circuit closes after successful probe in HALF_OPEN state.
    
    Contract: When circuit is HALF_OPEN:
    1. Successful call resets failure count to 0
    2. Circuit transitions back to CLOSED
    3. Normal operation resumes
    """
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=1)
    
    # Open the circuit
    failing_func = Mock(side_effect=RuntimeError("API error"))
    for _ in range(3):
        with pytest.raises(RuntimeError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for cooldown
    time.sleep(1.1)
    
    # Successful probe should close circuit
    success_func = Mock(return_value="recovered")
    result = breaker.call(success_func)
    
    assert result == "recovered"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.last_failure_time is None


def test_circuit_reopens_if_probe_fails():
    """Test circuit reopens if probe fails in HALF_OPEN state.
    
    Contract: When circuit is HALF_OPEN and probe fails:
    1. Failure count increments
    2. Circuit immediately returns to OPEN
    3. New cooldown period starts
    """
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=1)
    
    # Open the circuit
    failing_func = Mock(side_effect=RuntimeError("API error"))
    for _ in range(3):
        with pytest.raises(RuntimeError):
            breaker.call(failing_func)
    
    # Wait for cooldown
    time.sleep(1.1)
    
    # Probe fails - should reopen circuit
    with pytest.raises(RuntimeError):
        breaker.call(failing_func)
    
    # Circuit should be OPEN again with new cooldown
    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count == 4  # Original 3 + 1 failed probe
    
    # Immediate retry should be blocked
    with pytest.raises(CircuitBreakerOpenError):
        breaker.call(failing_func)


def test_success_resets_failure_count():
    """Test successful call resets failure count before threshold.
    
    Contract: When circuit is CLOSED:
    1. Failures increment counter
    2. Success resets counter to 0
    3. Circuit remains CLOSED
    """
    breaker = CircuitBreaker(failure_threshold=5)
    
    failing_func = Mock(side_effect=RuntimeError("API error"))
    success_func = Mock(return_value="ok")
    
    # 3 failures (below threshold)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            breaker.call(failing_func)
    
    assert breaker.failure_count == 3
    assert breaker.state == CircuitState.CLOSED  # Still closed
    
    # Success resets counter
    result = breaker.call(success_func)
    assert result == "ok"
    assert breaker.failure_count == 0
    assert breaker.state == CircuitState.CLOSED


def test_custom_failure_threshold():
    """Test circuit breaker with custom failure threshold.
    
    Contract: Circuit opens after reaching custom threshold.
    """
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    
    failing_func = Mock(side_effect=ValueError("Custom error"))
    
    # 2 failures - should not open
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 2
    
    # 3rd failure - should open
    with pytest.raises(ValueError):
        breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count == 3


def test_custom_cooldown_period():
    """Test circuit breaker with custom cooldown period.
    
    Contract: Circuit waits for custom cooldown before allowing probe.
    """
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=2)
    
    failing_func = Mock(side_effect=RuntimeError("Error"))
    
    # Open circuit
    for _ in range(2):
        with pytest.raises(RuntimeError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait 1 second (less than cooldown)
    time.sleep(1)
    
    # Should still be blocked
    with pytest.raises(CircuitBreakerOpenError):
        breaker.call(failing_func)
    
    # Wait another 1.1 seconds (total > 2s cooldown)
    time.sleep(1.1)
    
    # Should allow probe now
    success_func = Mock(return_value="recovered")
    result = breaker.call(success_func)
    assert result == "recovered"
    assert breaker.state == CircuitState.CLOSED
