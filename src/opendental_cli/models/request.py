"""Request Data Models."""

from pydantic import BaseModel, Field, field_validator


class AuditDataRequest(BaseModel):
    """User request for audit data retrieval."""

    patnum: int = Field(gt=0, description="Patient Number (must be positive integer)")
    aptnum: int = Field(gt=0, description="Appointment Number (must be positive integer)")
    output_file: str | None = Field(None, description="Optional output file path")
    redact_phi: bool = Field(False, description="Whether to redact PHI in output")
    force_overwrite: bool = Field(False, description="Skip confirmation for existing output file")

    @field_validator("patnum", "aptnum")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that PatNum and AptNum are positive integers.

        Args:
            v: Value to validate

        Returns:
            Validated value

        Raises:
            ValueError: If value is not positive
        """
        if v <= 0:
            raise ValueError("PatNum and AptNum must be positive integers")
        return v
