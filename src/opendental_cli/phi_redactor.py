"""PHI Redactor for Output.

Redacts PHI fields in output JSON while preserving structure for debugging.
Used when --redact-phi flag is set.

Article II Compliance: Output Redaction Rule
"""

from typing import Any


class PHIRedactor:
    """Redacts PHI from output data structures."""

    # PHI field names to redact
    PHI_FIELDS = {
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
        "ProcDate",
        "DateService",
        "DateStatement",
        "EntryDateTime",
        "Note",
    }

    def redact(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact PHI fields in data structure.

        Args:
            data: Dictionary to redact

        Returns:
            Redacted dictionary with PHI replaced by [REDACTED]
        """
        return self._redact_recursive(data)

    def _redact_recursive(self, obj: Any) -> Any:
        """Recursively process object to redact PHI.

        Args:
            obj: Object to process (dict, list, or primitive)

        Returns:
            Redacted object
        """
        if isinstance(obj, dict):
            return {key: self._redact_value(key, value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._redact_recursive(item) for item in obj]
        else:
            return obj

    def _redact_value(self, key: str, value: Any) -> Any:
        """Redact value if key is PHI field.

        Args:
            key: Field name
            value: Field value

        Returns:
            [REDACTED] if PHI field, otherwise recursively process value
        """
        if key in self.PHI_FIELDS:
            return "[REDACTED]"
        return self._redact_recursive(value)
