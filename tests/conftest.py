"""Shared pytest fixtures and configuration."""

import pytest
from pydantic import SecretStr

from opendental_cli.models.credential import APICredential


@pytest.fixture
def sample_credentials():
    """Provide sample API credentials for testing."""
    return APICredential(
        base_url="https://example.opendental.com/api/v1",
        developer_key=SecretStr("test-developer-key-12345"),
        customer_key=SecretStr("test-customer-key-12345"),
        environment="production",
    )


@pytest.fixture
def sample_patient_data():
    """Provide sample patient response data."""
    return {
        "PatNum": 12345,
        "FName": "John",
        "LName": "Doe",
        "MiddleI": "M",
        "Birthdate": "1985-03-15",
        "SSN": "123-45-6789",
        "Gender": "M",
        "Address": "123 Main St",
        "City": "Springfield",
        "State": "IL",
        "Zip": "62701",
        "HmPhone": "(555) 123-4567",
        "WkPhone": "(555) 987-6543",
        "Email": "john.doe@example.com",
    }


@pytest.fixture
def sample_appointment_data():
    """Provide sample appointment response data."""
    return {
        "AptNum": 67890,
        "PatNum": 12345,
        "AptDateTime": "2025-11-29T14:30:00Z",
        "ProvNum": 5,
        "ProvName": "Dr. Smith",
        "ClinicNum": 1,
        "AptStatus": "Scheduled",
        "Confirmed": True,
        "Note": "Routine checkup",
    }
