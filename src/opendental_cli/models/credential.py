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
        """Generate Authorization header for OpenDental FHIR API.

        OpenDental FHIR API uses the ODFHIR authentication scheme with format:
        Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}

        This method constructs the required Authorization header by combining
        the developer_key and customer_key (portal key) in the ODFHIR format.

        SecretStr ensures credential values are not exposed in logs or traces.

        Returns:
            dict[str, str]: Dictionary with single 'Authorization' header
                          in format: "ODFHIR {key1}/{key2}"
        """
        developer_key = self.developer_key.get_secret_value()
        portal_key = self.customer_key.get_secret_value()
        return {
            "Authorization": f"ODFHIR {developer_key}/{portal_key}"
        }
