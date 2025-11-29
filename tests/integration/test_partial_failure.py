"""Integration tests for partial failure scenarios.

Tests system behavior when some endpoints fail while others succeed.
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
def test_partial_failure_one_endpoint(mock_get_creds, mock_credentials, fixtures_dir):
    """Test partial failure with 1 endpoint failing, 5 succeeding."""
    mock_get_creds.return_value = mock_credentials

    # Mock 5 endpoints to succeed
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
    # Diseases endpoint fails with 503
    respx.get("https://example.opendental.com/api/v1/diseases?PatNum=12345").mock(
        return_value=httpx.Response(
            503, json=load_fixture(fixtures_dir, "appointment_503.json")
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

    # Verify exit code 2 (partial failure)
    assert result.exit_code == 2

    # Verify output mentions partial success
    assert "Partial success" in result.output or "some endpoints failed" in result.output


@respx.mock
@patch("opendental_cli.cli.get_credentials")
def test_complete_failure_all_endpoints(mock_get_creds, mock_credentials):
    """Test complete failure when all endpoints fail."""
    mock_get_creds.return_value = mock_credentials

    # Mock all endpoints to fail with 500
    respx.get("https://example.opendental.com/api/v1/procedurelogs?AptNum=67890").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )
    respx.get("https://example.opendental.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )
    respx.get("https://example.opendental.com/api/v1/medicationpats?PatNum=12345").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )
    respx.get("https://example.opendental.com/api/v1/diseases?PatNum=12345").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )
    respx.get("https://example.opendental.com/api/v1/patientnotes/12345").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )
    respx.put(
        "https://example.opendental.com/api/v1/queries/ShortQuery"
    ).mock(return_value=httpx.Response(500, json={"error": "Internal server error"}))

    runner = CliRunner()
    result = runner.invoke(main, ["--patnum", "12345", "--aptnum", "67890"])

    # Verify exit code 1 (complete failure)
    assert result.exit_code == 1

    # Verify output mentions failure
    assert "All endpoints failed" in result.output or "failed" in result.output.lower()


@respx.mock
@patch("opendental_cli.cli.get_credentials")
def test_partial_failure_with_output_file(
    mock_get_creds, mock_credentials, fixtures_dir, tmp_path
):
    """Test partial failure output contains both success and failures sections."""
    mock_get_creds.return_value = mock_credentials

    # Mock 4 success, 2 failures
    respx.get("https://example.opendental.com/api/v1/procedurelogs?AptNum=67890").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "patient_12345.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    respx.get("https://example.opendental.com/api/v1/medicationpats?PatNum=12345").mock(
        return_value=httpx.Response(
            200, json=load_fixture(fixtures_dir, "treatment_success.json")
        )
    )
    respx.get("https://example.opendental.com/api/v1/diseases?PatNum=12345").mock(
        return_value=httpx.Response(503, json={"error": "Service unavailable"})
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

    output_file = tmp_path / "partial.json"

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--patnum", "12345", "--aptnum", "67890", "--output", str(output_file)],
    )

    # Verify exit code 2
    assert result.exit_code == 2

    # Verify file contains both success and failures
    content = json.loads(output_file.read_text())
    assert len(content["success"]) == 4  # 4 successful endpoints
    assert len(content["failures"]) == 2  # 2 failed endpoints
    assert content["successful_count"] == 4
    assert content["failed_count"] == 2

    # Verify failure details
    failure_endpoints = [f["endpoint"] for f in content["failures"]]
    assert "allergies" in failure_endpoints
    assert "diseases" in failure_endpoints
