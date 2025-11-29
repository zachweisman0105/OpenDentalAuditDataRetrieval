"""Audit Log Entry Model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Single audit log record (NO PHI).

    Used for HIPAA compliance audit trail.
    """

    timestamp: datetime = Field(
        default_factory=lambda: datetime.utcnow(), description="Log entry timestamp (UTC)"
    )
    operation_type: str = Field(description="Operation type (e.g., 'fetch_patient', 'fetch_appointment')")
    endpoint: str = Field(description="API endpoint path (NO PatNum/AptNum values)")
    http_status: int = Field(description="HTTP response status code")
    success: bool = Field(description="Whether operation succeeded")
    duration_ms: float = Field(description="Operation duration in milliseconds")
    error_category: Optional[str] = Field(None, description="Error category if failed (e.g., 'timeout', 'not_found')")

    # Explicitly NO PHI fields:
    # - No patient names, DOBs, SSNs
    # - No PatNum/AptNum values (only in operation_type context)
    # - No provider names
    # - No clinical data
