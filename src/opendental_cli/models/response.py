"""Response Data Models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from opendental_cli.models.request import AuditDataRequest


class EndpointResponse(BaseModel):
    """Response from a single OpenDental API endpoint."""

    endpoint_name: str = Field(description="Endpoint identifier (e.g., 'patient', 'appointment')")
    http_status: int = Field(description="HTTP status code (200, 404, 500, etc.)")
    success: bool = Field(description="Whether request succeeded")
    data: dict[str, Any] | list[dict[str, Any]] | None = Field(
        None, description="Parsed JSON response - dict for single resource, list for collections (None if failed)"
    )
    error_message: str | None = Field(None, description="Error description (non-PHI)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.utcnow(), description="Response timestamp (UTC)"
    )
    duration_ms: float = Field(description="Request duration in milliseconds")

    def is_retriable(self) -> bool:
        """Check if this failure should be retried (5xx or network error).

        Returns:
            True if retriable, False otherwise
        """
        return (not self.success) and (self.http_status >= 500 or self.http_status == 0)


class ConsolidatedAuditData(BaseModel):
    """Consolidated audit data from multiple endpoints."""

    request: AuditDataRequest = Field(description="Original request parameters")
    success: dict[str, dict[str, Any] | list[dict[str, Any]]] = Field(
        default_factory=dict, description="Successful endpoint responses - dict for single resource, list for collections"
    )
    failures: list[dict[str, str]] = Field(
        default_factory=list, description="Failed endpoint details"
    )
    total_endpoints: int = Field(description="Total number of endpoints queried")
    successful_count: int = Field(description="Number of successful responses")
    failed_count: int = Field(description="Number of failed responses")
    retrieval_timestamp: datetime = Field(
        default_factory=lambda: datetime.utcnow(), description="Data retrieval timestamp (UTC)"
    )

    def exit_code(self) -> int:
        """Determine appropriate exit code.

        Returns:
            0 (all success), 1 (all failed), 2 (partial)
        """
        if self.failed_count == 0:
            return 0  # All success
        elif self.successful_count == 0:
            return 1  # All failed
        else:
            return 2  # Partial success

    def apply_phi_redaction(self) -> "ConsolidatedAuditData":
        """Return new instance with PHI redacted in success data.

        Returns:
            ConsolidatedAuditData with redacted PHI
        """
        from opendental_cli.phi_redactor import PHIRedactor

        redactor = PHIRedactor()
        redacted_success = {endpoint: redactor.redact(data) for endpoint, data in self.success.items()}
        return self.model_copy(update={"success": redacted_success})
