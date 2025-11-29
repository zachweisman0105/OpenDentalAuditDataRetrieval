"""Integration tests for PHI redaction feature.

Tests --redact-phi flag with full CLI execution.
"""

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx
from click.testing import CliRunner

from opendental_cli.cli import main
from opendental_cli.models.credential import APICredential


@pytest.fixture
def mock_credentials():
    """Mock credential retrieval."""
    return APICredential(
        base_url="https://example.opendental.com/api/v1",
        developer_key="test_developer_key",
        customer_key="test_customer_key",
        environment="production",
    )


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory path."""
    return Path(__file__).parent.parent / "fixtures"


def load_fixture(fixtures_dir: Path, filename: str) -> dict:
    """Load JSON fixture file."""
    return json.loads((fixtures_dir / filename).read_text())


@respx.mock
@patch("opendental_cli.cli.get_credentials")
def test_redact_phi_stdout(mock_get_creds, mock_credentials, fixtures_dir):
    """Test --redact-phi flag with stdout output."""
    mock_get_creds.return_value = mock_credentials

    # Mock all 6 endpoints
    respx.get("https://example.opendental.com/api/v1/procedurelogs?AptNum=67890").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "patient_12345.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "appointment_67890.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/medicationpats?PatNum=12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "treatment_success.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/diseases?PatNum=12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "billing_success.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/patientnotes/12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "insurance_success.json")
        )
    )
    respx.put(
        "https://example.opendental.com/api/v1/queries/ShortQuery"
    ).mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "clinical_notes_success.json")
        )
    )

    runner = CliRunner()
    result = runner.invoke(
        main, ["--patnum", "12345", "--aptnum", "67890", "--redact-phi"]
    )

    # Verify exit code 0
    assert result.exit_code == 0

    # Verify output contains [REDACTED]
    assert "[REDACTED]" in result.output

    # Verify no actual PHI in output
    assert "John" not in result.output  # FName
    assert "Doe" not in result.output  # LName
    assert "123-45-6789" not in result.output  # SSN
    assert "john.doe@example.com" not in result.output  # Email


@respx.mock
@patch("opendental_cli.cli.get_credentials")
def test_redact_phi_file_output(
    mock_get_creds, mock_credentials, fixtures_dir, tmp_path
):
    """Test --redact-phi with file output."""
    mock_get_creds.return_value = mock_credentials

    # Mock all 6 endpoints
    respx.get("https://example.opendental.com/api/v1/procedurelogs?AptNum=67890").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "patient_12345.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "appointment_67890.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/medicationpats?PatNum=12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "treatment_success.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/diseases?PatNum=12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "billing_success.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/patientnotes/12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "insurance_success.json")
        )
    )
    respx.put(
        "https://example.opendental.com/api/v1/queries/ShortQuery"
    ).mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "clinical_notes_success.json")
        )
    )

    output_file = tmp_path / "audit_redacted.json"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--patnum",
            "12345",
            "--aptnum",
            "67890",
            "--redact-phi",
            "--output",
            str(output_file),
        ],
    )

    # Verify exit code 0
    assert result.exit_code == 0

    # Verify file exists
    assert output_file.exists()

    # Verify file content has redacted PHI
    content = json.loads(output_file.read_text())

    # Check patient data is redacted
    patient_data = content["success"]["patient"]
    assert patient_data["FName"] == "[REDACTED]"
    assert patient_data["LName"] == "[REDACTED]"
    assert patient_data["Birthdate"] == "[REDACTED]"
    assert patient_data["SSN"] == "[REDACTED]"
    assert patient_data["Email"] == "[REDACTED]"

    # Check PatNum is NOT redacted (not PHI)
    assert patient_data["PatNum"] == 12345

    # Check appointment data is redacted
    apt_data = content["success"]["appointment"]
    assert apt_data["AptDateTime"] == "[REDACTED]"
    assert apt_data["ProvName"] == "[REDACTED]"
    assert apt_data["Note"] == "[REDACTED]"

    # Check AptNum is NOT redacted
    assert apt_data["AptNum"] == 67890
