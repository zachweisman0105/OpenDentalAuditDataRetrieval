"""Contract tests for API client golden path.

Tests all 6 OpenDental API endpoints with respx mocking 200 OK responses.
Uses real JSON fixtures matching contract schemas.
"""

import json
from pathlib import Path

import httpx
import pytest
import respx

from opendental_cli.api_client import OpenDentalAPIClient
from opendental_cli.models.credential import APICredential


@pytest.fixture
def api_credential():
    """Create test API credential."""
    return APICredential(
        base_url="https://example.opendental.com/api/v1",
        developer_key="test_developer_key_12345",
        customer_key="test_customer_key_12345",
        environment="production",
    )


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory path."""
    return Path(__file__).parent.parent / "fixtures"


def load_fixture(fixtures_dir: Path, filename: str) -> dict:
    """Load JSON fixture file."""
    return json.loads((fixtures_dir / filename).read_text())


@pytest.mark.asyncio
@respx.mock
async def test_fetch_procedure_logs_golden_path(api_credential, fixtures_dir):
    """Test procedurelogs endpoint with 200 OK response."""
    procedure_logs_data = load_fixture(fixtures_dir, "patient_12345.json")

    # Mock procedurelogs endpoint
    route = respx.get("https://example.opendental.com/api/v1/procedurelogs?AptNum=67890").mock(
        return_value=httpx.Response(200, json=procedure_logs_data)
    )

    client = OpenDentalAPIClient(api_credential)
    try:
        response = await client.fetch_procedure_logs(67890)

        assert response.success is True
        assert response.http_status == 200
        assert response.endpoint_name == "procedurelogs"
        assert response.data == procedure_logs_data
        assert response.error_message is None
        assert route.called
        
        # Verify Authorization header with ODFHIR format
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("ODFHIR ")
        assert "/" in request.headers["Authorization"]
        assert "test_developer_key_12345" in request.headers["Authorization"]
        assert "test_customer_key_12345" in request.headers["Authorization"]
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_fetch_allergies_golden_path(api_credential, fixtures_dir):
    """Test allergies endpoint with 200 OK response."""
    allergies_data = load_fixture(fixtures_dir, "appointment_67890.json")

    route = respx.get("https://example.opendental.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(200, json=allergies_data)
    )

    client = OpenDentalAPIClient(api_credential)
    try:
        response = await client.fetch_allergies(12345)

        assert response.success is True
        assert response.http_status == 200
        assert response.endpoint_name == "allergies"
        assert response.data == allergies_data
        assert route.called
        
        # Verify Authorization header with ODFHIR format
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("ODFHIR ")
        assert "/" in request.headers["Authorization"]
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_fetch_medications_golden_path(api_credential, fixtures_dir):
    """Test medicationpats endpoint with 200 OK response."""
    medications_data = load_fixture(fixtures_dir, "treatment_success.json")

    route = respx.get(
        "https://example.opendental.com/api/v1/medicationpats?PatNum=12345"
    ).mock(return_value=httpx.Response(200, json=medications_data))

    client = OpenDentalAPIClient(api_credential)
    try:
        response = await client.fetch_medications(12345)

        assert response.success is True
        assert response.http_status == 200
        assert response.endpoint_name == "medicationpats"
        assert response.data == medications_data
        assert route.called
        
        # Verify Authorization header with ODFHIR format
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("ODFHIR ")
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_fetch_problems_golden_path(api_credential, fixtures_dir):
    """Test diseases endpoint with 200 OK response."""
    problems_data = load_fixture(fixtures_dir, "billing_success.json")

    route = respx.get(
        "https://example.opendental.com/api/v1/diseases?PatNum=12345"
    ).mock(return_value=httpx.Response(200, json=problems_data))

    client = OpenDentalAPIClient(api_credential)
    try:
        response = await client.fetch_problems(12345)

        assert response.success is True
        assert response.http_status == 200
        assert response.endpoint_name == "diseases"
        assert response.data == problems_data
        assert route.called
        
        # Verify Authorization header with ODFHIR format
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("ODFHIR ")
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_fetch_patient_notes_golden_path(api_credential, fixtures_dir):
    """Test patientnotes endpoint with 200 OK response."""
    patient_notes_data = load_fixture(fixtures_dir, "insurance_success.json")

    route = respx.get("https://example.opendental.com/api/v1/patientnotes/12345").mock(
        return_value=httpx.Response(200, json=patient_notes_data)
    )

    client = OpenDentalAPIClient(api_credential)
    try:
        response = await client.fetch_patient_notes(12345)

        assert response.success is True
        assert response.http_status == 200
        assert response.endpoint_name == "patientnotes"
        assert response.data == patient_notes_data
        assert route.called
        
        # Verify Authorization header with ODFHIR format
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("ODFHIR ")
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_fetch_vital_signs_golden_path(api_credential, fixtures_dir):
    """Test vital_signs endpoint with 200 OK response (PUT request)."""
    vital_signs_data = load_fixture(fixtures_dir, "clinical_notes_success.json")

    route = respx.put(
        "https://example.opendental.com/api/v1/queries/ShortQuery"
    ).mock(return_value=httpx.Response(200, json=vital_signs_data))

    client = OpenDentalAPIClient(api_credential)
    try:
        response = await client.fetch_vital_signs(67890)

        assert response.success is True
        assert response.http_status == 200
        assert response.endpoint_name == "vital_signs"
        assert response.data == vital_signs_data
        assert route.called
        
        # Verify Authorization header with ODFHIR format
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("ODFHIR ")
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_all_endpoints_golden_path(api_credential, fixtures_dir):
    """Test all 6 endpoints succeed concurrently."""
    # Mock all endpoints
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

    client = OpenDentalAPIClient(api_credential)
    try:
        # Fetch all endpoints
        import asyncio

        results = await asyncio.gather(
            client.fetch_procedure_logs(67890),
            client.fetch_allergies(12345),
            client.fetch_medications(12345),
            client.fetch_problems(12345),
            client.fetch_patient_notes(12345),
            client.fetch_vital_signs(67890),
        )

        # All should succeed
        assert len(results) == 6
        for result in results:
            assert result.success is True
            assert result.http_status == 200
            assert result.data is not None

    finally:
        await client.close()
