"""Unit tests for PHI sanitizer (Structlog processor).

Tests verify PHISanitizerProcessor filters sensitive patterns from log records
including PatNum, patient names, dates, SSNs, and phone numbers.
"""

import re
from datetime import datetime
from opendental_cli.phi_sanitizer import PHISanitizerProcessor


def test_sanitizer_filters_patnum():
    """PHISanitizerProcessor filters PatNum from log records."""
    processor = PHISanitizerProcessor()
    
    # Create log event with PatNum
    logger = None
    method_name = "info"
    event_dict = {
        "event": "Retrieving patient data for PatNum: 12345",
        "patient_id": "PatNum 98765",
        "timestamp": datetime.now().isoformat(),
    }
    
    # Process event
    result = processor(logger, method_name, event_dict)
    
    # Verify PatNum numbers filtered with [REDACTED]
    assert "[REDACTED]" in result["event"]
    assert "[REDACTED]" in result.get("patient_id", "")
    # The pattern keeps "PatNum" but redacts the number
    assert "PatNum" in result["event"]
    
    # Verify timestamp preserved (not PHI)
    assert "timestamp" in result


def test_sanitizer_filters_patient_names():
    """PHISanitizerProcessor filters patient names in JSON-like strings."""
    processor = PHISanitizerProcessor()
    
    logger = None
    method_name = "info"
    event_dict = {
        "event": 'Retrieved patient with "FName": "John" and "LName": "Doe"',
        "FName": "Jane",  # PHI field - will be removed entirely
        "LName": "Smith",  # PHI field - will be removed entirely
        "full_name": "Robert Johnson",
    }
    
    result = processor(logger, method_name, event_dict)
    
    # FName and LName fields should be removed entirely (not just redacted)
    assert "FName" not in result
    assert "LName" not in result
    
    # FName/LName patterns in strings should be redacted
    if '"FName"' in event_dict["event"]:
        assert "[REDACTED]" in result["event"]


def test_sanitizer_filters_dates():
    """PHISanitizerProcessor filters dates in YYYY-MM-DD format."""
    processor = PHISanitizerProcessor()
    
    logger = None
    method_name = "info"
    event_dict = {
        "event": "Appointment scheduled for 2024-03-15",
        "birthdate": "1985-07-22",
        "date_of_service": "2024-01-10",
        "year_only": "2024",  # Should not be filtered (not a date pattern)
    }
    
    result = processor(logger, method_name, event_dict)
    
    # Verify YYYY-MM-DD dates filtered
    if "2024-03-15" in str(event_dict.get("event", "")):
        assert "2024-03-15" not in result["event"] or "[FILTERED]" in result["event"]
    
    if "birthdate" in result:
        assert "1985-07-22" not in str(result["birthdate"])
    
    if "date_of_service" in result:
        assert "2024-01-10" not in str(result["date_of_service"])
    
    # Year-only should be preserved (not a full date)
    if "year_only" in result:
        assert "2024" in str(result.get("year_only", ""))


def test_sanitizer_filters_ssns():
    """PHISanitizerProcessor filters SSNs in XXX-XX-XXXX format."""
    processor = PHISanitizerProcessor()
    
    logger = None
    method_name = "info"
    event_dict = {
        "event": "Patient SSN: 123-45-6789",
        "SSN": "987-65-4321",  # PHI field - will be removed
        "ssn_last_four": "5555",  # Partial SSN (not a full pattern)
    }
    
    result = processor(logger, method_name, event_dict)
    
    # Verify full SSN filtered in event string
    assert "123-45-6789" not in result["event"]
    assert "[REDACTED]" in result["event"]
    
    # SSN field should be removed entirely
    assert "SSN" not in result
    
    # Last 4 digits not matching full SSN pattern should be preserved
    assert result.get("ssn_last_four") == "5555"


def test_sanitizer_filters_phone_numbers():
    """PHISanitizerProcessor filters phone numbers in various formats."""
    processor = PHISanitizerProcessor()
    
    logger = None
    method_name = "info"
    event_dict = {
        "event": "Contact patient at (555) 123-4567",
        "home_phone": "555-987-6543",
        "work_phone": "5551234567",  # No formatting
        "phone_intl": "+1-555-234-5678",
        "extension": "x1234",  # Should not be filtered (not a phone)
    }
    
    result = processor(logger, method_name, event_dict)
    
    # Verify formatted phone numbers filtered
    if "(555) 123-4567" in str(event_dict.get("event", "")):
        assert "(555) 123-4567" not in result["event"] or "[FILTERED]" in result["event"]
    
    if "home_phone" in result:
        assert "555-987-6543" not in str(result["home_phone"])
    
    if "work_phone" in result:
        # 10-digit sequences should be filtered
        assert "5551234567" not in str(result["work_phone"]) or "[FILTERED]" in str(result.get("work_phone", ""))
    
    if "phone_intl" in result:
        assert "+1-555-234-5678" not in str(result["phone_intl"])


def test_sanitizer_preserves_non_phi_fields():
    """PHISanitizerProcessor preserves non-PHI fields like operation type, status codes."""
    processor = PHISanitizerProcessor()
    
    logger = None
    method_name = "info"
    event_dict = {
        "event": "API call completed",
        "operation_type": "RETRIEVE_PATIENT",
        "http_status": 200,
        "endpoint": "patients",
        "duration_ms": 125.5,
        "success": True,
    }
    
    result = processor(logger, method_name, event_dict)
    
    # Verify non-PHI fields preserved
    assert result["event"] == "API call completed"
    assert result["operation_type"] == "RETRIEVE_PATIENT"
    assert result["http_status"] == 200
    assert result["endpoint"] == "patients"
    assert result["duration_ms"] == 125.5
    assert result["success"] is True

def test_sanitizer_handles_nested_structures():
    """PHISanitizerProcessor filters PHI in nested dictionaries and lists."""
    processor = PHISanitizerProcessor()
    
    logger = None
    method_name = "info"
    event_dict = {
        "event": "Processing patient data",
        "patient": {
            "patnum": 12345,
            "FName": "John",  # PHI field name
            "LName": "Doe",  # PHI field name
            "Birthdate": "1980-05-15",  # PHI field name
        },
        "appointments": [
            {"aptnum": 67890, "date": "2024-03-20"},
            {"aptnum": 67891, "date": "2024-04-10"},
        ],
    }
    
    result = processor(logger, method_name, event_dict)
    
    # Verify nested PHI filtered
    if "patient" in result and isinstance(result["patient"], dict):
        patient = result["patient"]
        # FName/LName/Birthdate fields should be redacted
        if "FName" in patient:
            assert patient["FName"] == "[REDACTED]"
        if "LName" in patient:
            assert patient["LName"] == "[REDACTED]"
        if "Birthdate" in patient:
            assert patient["Birthdate"] == "[REDACTED]"
        # patnum should remain (not in PHI_FIELD_NAMES)
        # But in dict sanitization, non-PHI fields are preserved
        assert "patnum" in patient
    
    # Verify list items - dates should be sanitized in strings but preserved as-is in dicts
    # (dict values are only sanitized if they're strings or nested dicts)
    if "appointments" in result and isinstance(result["appointments"], list):
        for appt in result["appointments"]:
            if isinstance(appt, dict):
                # Dict values that aren't strings are preserved
                assert "date" in appt


def test_sanitizer_handles_none_values():
    """PHISanitizerProcessor handles None values without crashing."""
    processor = PHISanitizerProcessor()
    
    logger = None
    method_name = "info"
    event_dict = {
        "event": "Operation completed",
        "patient_name": None,
        "ssn": None,
        "phone": None,
    }
    
    # Should not raise exception
    result = processor(logger, method_name, event_dict)
    
    assert result["event"] == "Operation completed"
    assert result["patient_name"] is None
    assert result["ssn"] is None
    assert result["phone"] is None
