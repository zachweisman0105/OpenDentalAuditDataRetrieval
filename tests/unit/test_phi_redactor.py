"""Unit tests for PHI redactor.

Tests redaction of PHI fields in output JSON structures.
"""

import pytest

from opendental_cli.phi_redactor import PHIRedactor


class TestPHIRedactor:
    """Test PHIRedactor class."""

    def test_redact_patient_data(self):
        """Test redacting patient PHI fields."""
        redactor = PHIRedactor()
        data = {
            "PatNum": 12345,
            "FName": "John",
            "LName": "Doe",
            "Birthdate": "1985-03-15",
            "SSN": "123-45-6789",
            "Gender": "M",
            "Address": "123 Main St",
            "City": "Springfield",
            "HmPhone": "(555) 123-4567",
            "Email": "john@example.com",
        }

        result = redactor.redact(data)

        # PHI fields should be redacted
        assert result["FName"] == "[REDACTED]"
        assert result["LName"] == "[REDACTED]"
        assert result["Birthdate"] == "[REDACTED]"
        assert result["SSN"] == "[REDACTED]"
        assert result["Address"] == "[REDACTED]"
        assert result["City"] == "[REDACTED]"
        assert result["HmPhone"] == "[REDACTED]"
        assert result["Email"] == "[REDACTED]"

        # Non-PHI fields should be preserved
        assert result["PatNum"] == 12345
        assert result["Gender"] == "M"

    def test_redact_nested_structures(self):
        """Test redacting PHI in nested JSON structures."""
        redactor = PHIRedactor()
        data = {
            "patient": {
                "FName": "Jane",
                "LName": "Smith",
                "PatNum": 67890,
            },
            "procedures": [
                {
                    "ProcNum": 101,
                    "ProcDate": "2025-01-15",
                    "Note": "Regular checkup",
                },
                {
                    "ProcNum": 102,
                    "ProcDate": "2024-12-10",
                    "Note": "Cleaning",
                },
            ],
        }

        result = redactor.redact(data)

        # Nested PHI should be redacted
        assert result["patient"]["FName"] == "[REDACTED]"
        assert result["patient"]["LName"] == "[REDACTED]"
        assert result["patient"]["PatNum"] == 67890
        assert result["procedures"][0]["ProcDate"] == "[REDACTED]"
        assert result["procedures"][0]["Note"] == "[REDACTED]"
        assert result["procedures"][1]["ProcDate"] == "[REDACTED]"
        assert result["procedures"][1]["Note"] == "[REDACTED]"

        # Non-PHI preserved
        assert result["procedures"][0]["ProcNum"] == 101

    def test_redact_unicode_characters(self):
        """Test redacting PHI with Unicode characters."""
        redactor = PHIRedactor()
        data = {
            "FName": "José",
            "LName": "García",
            "Email": "josé@example.com",
            "PatNum": 99999,
        }

        result = redactor.redact(data)

        assert result["FName"] == "[REDACTED]"
        assert result["LName"] == "[REDACTED]"
        assert result["Email"] == "[REDACTED]"
        assert result["PatNum"] == 99999

    def test_redact_empty_values(self):
        """Test redacting empty PHI values."""
        redactor = PHIRedactor()
        data = {
            "FName": "",
            "LName": None,
            "PatNum": 12345,
        }

        result = redactor.redact(data)

        assert result["FName"] == "[REDACTED]"
        assert result["LName"] == "[REDACTED]"
        assert result["PatNum"] == 12345

    def test_redact_deeply_nested(self):
        """Test redacting deeply nested structures."""
        redactor = PHIRedactor()
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "FName": "Deep",
                        "LName": "Nested",
                        "PatNum": 11111,
                    }
                }
            }
        }

        result = redactor.redact(data)

        assert result["level1"]["level2"]["level3"]["FName"] == "[REDACTED]"
        assert result["level1"]["level2"]["level3"]["LName"] == "[REDACTED]"
        assert result["level1"]["level2"]["level3"]["PatNum"] == 11111

    def test_redact_appointment_data(self):
        """Test redacting appointment PHI."""
        redactor = PHIRedactor()
        data = {
            "AptNum": 67890,
            "PatNum": 12345,
            "AptDateTime": "2025-11-29T14:30:00Z",
            "ProvName": "Dr. Sarah Smith",
            "Note": "Regular checkup",
        }

        result = redactor.redact(data)

        assert result["AptDateTime"] == "[REDACTED]"
        assert result["ProvName"] == "[REDACTED]"
        assert result["Note"] == "[REDACTED]"
        assert result["AptNum"] == 67890
        assert result["PatNum"] == 12345

    def test_redact_preserves_structure(self):
        """Test that redaction preserves JSON structure."""
        redactor = PHIRedactor()
        data = {
            "success": {
                "patient": {
                    "FName": "Test",
                    "PatNum": 123,
                },
                "appointment": {
                    "AptDateTime": "2025-01-01",
                    "AptNum": 456,
                },
            },
            "failures": [],
        }

        result = redactor.redact(data)

        # Structure preserved
        assert "success" in result
        assert "patient" in result["success"]
        assert "appointment" in result["success"]
        assert "failures" in result
        assert isinstance(result["failures"], list)

        # PHI redacted
        assert result["success"]["patient"]["FName"] == "[REDACTED]"
        assert result["success"]["appointment"]["AptDateTime"] == "[REDACTED]"
