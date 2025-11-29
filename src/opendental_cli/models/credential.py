"""Credential Data Models."""

from pydantic import BaseModel, Field, HttpUrl, SecretStr


class APICredential(BaseModel):
    """OpenDental API credentials (NEVER log or display).

    Uses SecretStr to prevent accidental logging of API keys.
    Requires TWO keys for authentication:
    - Developer Key: Provided by OpenDental for API access
    - Customer Key: Customer-specific authentication key
    """

    base_url: HttpUrl = Field(description="OpenDental API base URL (e.g., https://server/api/v1)")
    developer_key: SecretStr = Field(description="Developer API key for OpenDental authentication")
    customer_key: SecretStr = Field(description="Customer-specific API key for authentication")
    environment: str = Field("production", description="Environment name (production, staging, dev)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "base_url": "https://example.opendental.com/api/v1",
                "developer_key": "***REDACTED***",
                "customer_key": "***REDACTED***",
                "environment": "production",
            }
        }
    }

    def get_auth_header(self) -> dict[str, str]:
        """Generate Authorization headers.

        SecretStr ensures keys not leaked in logs.
        Both developer_key and customer_key are required for API authentication.

        Returns:
            Authorization headers dict with both keys
        """
        return {
            "DeveloperKey": self.developer_key.get_secret_value(),
            "CustomerKey": self.customer_key.get_secret_value(),
        }
