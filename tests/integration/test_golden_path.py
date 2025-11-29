"""Integration tests for golden path CLI execution.

Tests full end-to-end workflow with mocked API responses.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

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
def test_golden_path_stdout(mock_get_creds, mock_credentials, fixtures_dir):
    """Test full CLI execution with stdout output."""
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
    result = runner.invoke(main, ["--patnum", "12345", "--aptnum", "67890"])

    # Verify exit code 0 (success)
    assert result.exit_code == 0

    # Verify output contains expected data
    assert "12345" in result.output
    assert "67890" in result.output
    assert "All endpoints succeeded" in result.output


@respx.mock
@patch("opendental_cli.cli.get_credentials")
def test_golden_path_file_output(mock_get_creds, mock_credentials, fixtures_dir, tmp_path):
    """Test full CLI execution with file output."""
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

    output_file = tmp_path / "audit.json"

    runner = CliRunner()
    result = runner.invoke(
        main, ["--patnum", "12345", "--aptnum", "67890", "--output", str(output_file)]
    )

    # Verify exit code 0
    assert result.exit_code == 0

    # Verify file was created
    assert output_file.exists()

    # Verify file content
    content = json.loads(output_file.read_text())
    assert content["request"]["patnum"] == 12345
    assert content["request"]["aptnum"] == 67890
    assert content["successful_count"] == 6
    assert content["failed_count"] == 0
    assert "procedurelogs" in content["success"]
    assert "allergies" in content["success"]

    # Verify output message
    assert "Output written to" in result.output
    assert "All endpoints succeeded" in result.output


@patch("opendental_cli.cli.get_credentials")
def test_missing_patnum(mock_get_creds):
    """Test error when patnum is missing."""
    runner = CliRunner()
    result = runner.invoke(main, ["--aptnum", "67890"])

    assert result.exit_code == 1
    assert "--patnum and --aptnum are required" in result.output


@patch("opendental_cli.cli.get_credentials")
def test_invalid_patnum_zero(mock_get_creds):
    """Test error when patnum is zero."""
    runner = CliRunner()
    result = runner.invoke(main, ["--patnum", "0", "--aptnum", "67890"])

    assert result.exit_code == 1
    assert "positive integers" in result.output


@patch("opendental_cli.cli.get_credentials")
def test_invalid_patnum_negative(mock_get_creds):
    """Test error when patnum is negative."""
    runner = CliRunner()
    result = runner.invoke(main, ["--patnum", "-1", "--aptnum", "67890"])

    assert result.exit_code == 1
    assert "positive integers" in result.output


@patch("opendental_cli.cli.get_credentials")
def test_no_credentials_configured(mock_get_creds):
    """Test error when credentials not configured."""
    from opendental_cli.credential_manager import CredentialNotFoundError

    mock_get_creds.side_effect = CredentialNotFoundError("No credentials found")

    runner = CliRunner()
    result = runner.invoke(main, ["--patnum", "12345", "--aptnum", "67890"])

    assert result.exit_code == 1
    assert "No credentials" in result.output
    assert "config set-credentials" in result.output
