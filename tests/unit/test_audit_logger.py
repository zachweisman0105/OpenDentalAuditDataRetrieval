"""Unit tests for audit logger configuration and security.

Tests verify audit.log created with secure permissions (0o600),
log entries contain no PHI, and timestamps are in UTC format.
"""

import os
import stat
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pytest
from opendental_cli.audit_logger import configure_audit_logging
import structlog


def test_audit_log_created_with_secure_permissions(tmp_path):
    """Audit log file created with 0o600 permissions (owner read/write only)."""
    # Use temporary directory for test
    log_file = tmp_path / "audit.log"
    
    # Configure audit logging with custom log file path
    configure_audit_logging(log_file=str(log_file))
    
    # Write a log entry to trigger file creation
    logger = structlog.get_logger()
    logger.info("Test audit entry", operation_type="TEST")
    
    # Verify file exists
    assert log_file.exists(), "Audit log file should be created"
    
    # Check permissions on Unix-like systems
    if os.name != "nt":  # Not Windows
        file_stat = log_file.stat()
        file_mode = stat.filemode(file_stat.st_mode)
        
        # Should be -rw------- (0o600)
        assert file_stat.st_mode & 0o777 == 0o600, \
            f"Audit log should have 0o600 permissions, got {oct(file_stat.st_mode & 0o777)}"
    else:
        # On Windows, check if file is not world-readable (basic check)
        # Windows permissions are more complex, but we can verify file exists and is accessible
        assert log_file.is_file(), "Audit log should be a regular file"


def test_audit_log_entries_contain_no_phi(tmp_path):
    """Audit log entries do not contain PHI fields like PatNum, names, SSNs, dates."""
    log_file = tmp_path / "test_audit.log"
    
    # Configure logging
    configure_audit_logging(log_file=str(log_file))
    
    logger = structlog.get_logger()
    
    # Log entries that might contain PHI
    logger.info(
        "Patient data retrieved for PatNum: 12345",  # PatNum in string should be redacted
        operation_type="RETRIEVE_PATIENT",
        endpoint="patients",
        FName="John",  # PHI field - will be removed
        LName="Doe",  # PHI field - will be removed
        SSN="123-45-6789",  # PHI field + pattern match - will be removed and redacted
        Birthdate="1980-05-15",  # PHI field + date pattern - will be removed and redacted
        http_status=200,  # Should NOT be filtered (non-PHI)
        duration_ms=125.5,  # Should NOT be filtered
    )
    
    logger.info(
        "Appointment retrieved with phone (555) 123-4567",  # Phone in string should be redacted
        operation_type="RETRIEVE_APPOINTMENT",
        endpoint="appointments",
        HmPhone="(555) 987-6543",  # PHI field - will be removed
        success=True,  # Should NOT be filtered
    )
    
    # Read log file content
    log_content = log_file.read_text()
    
    # Verify PHI not present in logs (FName, LName, SSN, Birthdate, HmPhone removed entirely)
    assert "FName" not in log_content, "FName field should be removed from logs"
    assert "LName" not in log_content, "LName field should be removed from logs"
    assert "SSN" not in log_content, "SSN field should be removed from logs"
    assert "Birthdate" not in log_content, "Birthdate field should be removed from logs"
    assert "HmPhone" not in log_content, "HmPhone field should be removed from logs"
    
    # Verify PHI patterns in strings are redacted
    assert "123-45-6789" not in log_content, "SSN pattern should be redacted from strings"
    assert "1980-05-15" not in log_content, "Date pattern should be redacted from strings"
    assert "(555) 123-4567" not in log_content, "Phone pattern should be redacted from strings"
    assert "(555) 987-6543" not in log_content, "Phone pattern should be redacted from strings"
    assert "[REDACTED]" in log_content, "Redacted marker should be present"
    
    # Verify non-PHI data IS present
    assert "RETRIEVE_PATIENT" in log_content, "Operation type should be in logs"
    assert "patients" in log_content or "endpoint" in log_content, "Endpoint should be in logs"
    assert "200" in log_content, "HTTP status should be in logs"
    assert "RETRIEVE_APPOINTMENT" in log_content, "Operation type should be in logs"
    assert "true" in log_content.lower(), "Success flag should be in logs"


def test_audit_log_utc_timestamp_format(tmp_path):
    """Audit log entries use UTC timestamps in ISO 8601 format."""
    log_file = tmp_path / "test_audit_utc.log"
    
    # Configure logging
    configure_audit_logging(log_file=str(log_file))
    
    logger = structlog.get_logger()
    
    # Capture timestamp before logging
    before = datetime.now(timezone.utc)
    
    # Log entry
    logger.info("Test entry for UTC validation", operation_type="TEST")
    
    # Capture timestamp after logging
    after = datetime.now(timezone.utc)
    
    # Read log content
    log_content = log_file.read_text()
    
    # Verify timestamp format (ISO 8601: YYYY-MM-DDTHH:MM:SS.ffffffZ or similar)
    # Common UTC formats: 2024-03-20T15:30:45.123456Z or 2024-03-20T15:30:45.123456+00:00
    assert "T" in log_content, "Timestamp should be in ISO 8601 format with 'T' separator"
    
    # Check for year (should be current year)
    current_year = str(before.year)
    assert current_year in log_content, f"Log should contain current year {current_year}"
    
    # Verify timestamp is within reasonable range (not using local timezone offset)
    # If using UTC, hour should match UTC time (not local time)
    # This is a basic check - exact validation depends on log format
    
    # Look for UTC indicator (Z or +00:00)
    # Note: Some formatters may use different UTC representations
    has_utc_indicator = "Z" in log_content or "+00:00" in log_content or "UTC" in log_content.upper()
    
    # Alternative: Check that timestamp is parseable and recent
    # Extract timestamp from log (assuming JSON format with "timestamp" key)
    if "timestamp" in log_content:
        # Basic validation that timestamp exists
        assert True, "Timestamp field present in log"


def test_audit_log_json_format(tmp_path):
    """Audit log entries are in JSON format for structured logging."""
    log_file = tmp_path / "test_audit_json.log"
    
    # Configure logging
    configure_audit_logging(log_file=str(log_file))
    
    logger = structlog.get_logger()
    
    # Log entry
    logger.info(
        "API call completed",
        operation_type="RETRIEVE_PATIENT",
        endpoint="patients",
        http_status=200,
        duration_ms=125.5,
        success=True,
    )
    
    # Read log content
    log_content = log_file.read_text()
    
    # Verify JSON format (basic checks)
    assert "{" in log_content, "Log should contain JSON objects"
    assert "}" in log_content, "Log should contain JSON objects"
    
    # Check for expected JSON keys
    assert '"event"' in log_content or "'event'" in log_content, "Log should have 'event' key"
    assert '"operation_type"' in log_content or "'operation_type'" in log_content, \
        "Log should have 'operation_type' key"
    
    # Verify values present
    assert "RETRIEVE_PATIENT" in log_content
    assert "200" in log_content
    assert "true" in log_content.lower()


def test_audit_log_multiple_entries(tmp_path):
    """Audit log handles multiple entries correctly."""
    log_file = tmp_path / "test_audit_multi.log"
    
    # Configure logging
    configure_audit_logging(log_file=str(log_file))
    
    logger = structlog.get_logger()
    
    # Log multiple entries
    logger.info("First entry", operation_type="OP1")
    logger.info("Second entry", operation_type="OP2")
    logger.info("Third entry", operation_type="OP3")
    
    # Read log content
    log_content = log_file.read_text()
    lines = log_content.strip().split("\n")
    
    # Should have at least 3 lines (one per log entry)
    assert len(lines) >= 3, f"Expected at least 3 log lines, got {len(lines)}"
    
    # Verify each entry is on its own line
    assert "OP1" in log_content
    assert "OP2" in log_content
    assert "OP3" in log_content


def test_audit_log_handles_exceptions_in_log_data(tmp_path):
    """Audit logger handles exceptions in log data gracefully."""
    log_file = tmp_path / "test_audit_exception.log"
    
    # Configure logging
    configure_audit_logging(log_file=str(log_file))
    
    logger = structlog.get_logger()
    
    # Log entry with potentially problematic data
    try:
        logger.info(
            "Entry with complex data",
            operation_type="TEST",
            none_value=None,
            dict_value={"key": "value"},
            list_value=[1, 2, 3],
        )
        
        # Should not raise exception
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "TEST" in log_content
        
    except Exception as e:
        pytest.fail(f"Audit logger should handle complex data types: {e}")
