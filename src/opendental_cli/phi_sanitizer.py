"""PHI Sanitizer for Structlog.

Filters Protected Health Information (PHI) from log records to ensure HIPAA compliance.
Removes patient names, DOBs, SSNs, phone numbers, and other sensitive data.

Article II Compliance: Logging Sanitization
"""

import re
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger


class PHISanitizerProcessor:
    """Structlog processor that sanitizes PHI from log messages."""

    # PHI patterns to redact
    PATTERNS = {
        # Patient/Appointment numbers (contextual - only in specific fields)
        "patnum": re.compile(r"\bPatNum[:\s=]+(\d+)", re.IGNORECASE),
        "aptnum": re.compile(r"\bAptNum[:\s=]+(\d+)", re.IGNORECASE),
        # SSN patterns (XXX-XX-XXXX or XXXXXXXXX)
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b"),
        # Phone numbers (various formats)
        "phone": re.compile(
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b"
        ),
        # Dates (YYYY-MM-DD, MM/DD/YYYY, etc.)
        "date": re.compile(
            r"\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b|\b\d{2}-\d{2}-\d{4}\b"
        ),
        # Email addresses
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        # Common name patterns in structured data
        "fname": re.compile(r'["\']FName["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE),
        "lname": re.compile(r'["\']LName["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE),
    }

    # Fields that should never appear in logs
    PHI_FIELD_NAMES = {
        "FName",
        "LName",
        "MiddleI",
        "Birthdate",
        "SSN",
        "Address",
        "City",
        "HmPhone",
        "WkPhone",
        "Email",
        "ProvName",
        "ProcDescript",
        "ToothNum",
        "NoteText",
        "Subscriber",
        "AptDateTime",
        "api_key",
        "Authorization",
    }

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        """Sanitize PHI from event dictionary.

        Args:
            logger: Wrapped logger instance
            method_name: Logging method name
            event_dict: Event dictionary to sanitize

        Returns:
            Sanitized event dictionary
        """
        # Sanitize event message
        if "event" in event_dict and isinstance(event_dict["event"], str):
            event_dict["event"] = self._sanitize_string(event_dict["event"])

        # Sanitize all string values in event dict
        for key, value in list(event_dict.items()):
            if isinstance(value, str):
                event_dict[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                event_dict[key] = self._sanitize_dict(value)

        # Remove PHI field names entirely
        for phi_field in self.PHI_FIELD_NAMES:
            event_dict.pop(phi_field, None)

        return event_dict

    def _sanitize_string(self, text: str) -> str:
        """Apply regex patterns to sanitize a string.

        Args:
            text: String to sanitize

        Returns:
            Sanitized string with PHI replaced by [REDACTED]
        """
        for pattern_name, pattern in self.PATTERNS.items():
            if pattern_name in ("patnum", "aptnum"):
                # Replace only the number, keep the field name
                text = pattern.sub(r"\g<0>=[REDACTED]", text)
            else:
                text = pattern.sub("[REDACTED]", text)
        return text

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively sanitize dictionary values.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        for key, value in data.items():
            if key in self.PHI_FIELD_NAMES:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized


def get_sanitizer() -> PHISanitizerProcessor:
    """Get PHI sanitizer processor instance.

    Returns:
        PHISanitizerProcessor instance
    """
    return PHISanitizerProcessor()
