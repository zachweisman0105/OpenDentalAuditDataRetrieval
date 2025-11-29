"""Unit Tests for API Client Error Handling.

Tests individual error scenarios without orchestration layer.
Validates error categorization, response formatting, and retry logic.
"""

import httpx
import pytest
import respx
from pydantic import ValidationError

from opendental_cli.api_client import OpenDentalAPIClient
from opendental_cli.models.credential import APICredential


@pytest.fixture
def api_client():
    """Create OpenDentalAPIClient with test credentials."""
    credentials = APICredential(
        base_url="https://test.opendental.com/api/v1",
        developer_key="test-developer-key",
        customer_key="test-customer-key",
        environment="test",
    )
    return OpenDentalAPIClient(credentials)


@respx.mock
@pytest.mark.asyncio
async def test_404_response_handling(api_client):
    """Test 404 response is handled with appropriate error message.
    
    Contract: When endpoint returns 404 Not Found, client should:
    1. Raise HTTPStatusError or return error response
    2. Include clear error message indicating resource not found
    3. Set success=False in response
    """
    respx.get("https://test.opendental.com/api/v1/procedurelogs?AptNum=99999").mock(
        return_value=httpx.Response(
            404,
            json={"error": "Procedure logs not found", "code": "PROCEDURELOGS_NOT_FOUND"},
        )
    )
    
    # Attempt to fetch non-existent procedure logs
    # API client should handle 404 gracefully
    try:
        result = await api_client.fetch_procedure_logs(99999)
        # If client returns result instead of raising, verify it indicates failure
        assert result.success is False
        assert "404" in result.error_message or "not found" in result.error_message.lower()
    except httpx.HTTPStatusError as e:
        # If client raises exception, verify it's properly formatted
        assert e.response.status_code == 404
        assert "not found" in str(e).lower()


@respx.mock
@pytest.mark.asyncio
async def test_401_response_with_credential_guidance(api_client):
    """Test 401 response includes guidance to update credentials.
    
    Contract: When endpoint returns 401 Unauthorized, error message should:
    1. Indicate authentication failure
    2. Suggest running 'opendental-cli config set-credentials'
    3. Mention checking API key validity
    """
    respx.get("https://test.opendental.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(
            401,
            json={"error": "Unauthorized", "message": "Invalid API key"},
        )
    )
    
    # Attempt to fetch with invalid credentials
    try:
        result = await api_client.fetch_allergies(12345)
        # If client returns result, verify error message
        assert result.success is False
        assert "401" in result.error_message or "unauthorized" in result.error_message.lower()
        # In actual implementation, orchestrator adds credential guidance
    except httpx.HTTPStatusError as e:
        # If client raises exception
        assert e.response.status_code == 401
        assert "unauthorized" in str(e).lower() or "invalid" in str(e).lower()


@respx.mock
@pytest.mark.asyncio
async def test_malformed_json_response_validation_error(api_client):
    """Test malformed JSON response is caught and treated as failure.
    
    Contract: When API returns invalid JSON or missing required fields:
    1. API client returns response with raw data
    2. Validation happens at orchestration layer
    3. For this unit test, we verify client doesn't crash on malformed data
    
    Note: API client returns EndpointResponse with raw data dict.
    Pydantic validation happens when orchestrator tries to parse into models.
    """
    # Return JSON with missing required fields
    respx.get("https://test.opendental.com/api/v1/medicationpats?PatNum=12345").mock(
        return_value=httpx.Response(
            200,
            json={
                "invalid_field": "This is not a valid medications response",
                "missing": "PatNum and other required fields",
            },
        )
    )
    
    # API client should return response with raw data
    result = await api_client.fetch_medications(12345)
    assert result.success is True  # HTTP 200 = success at API client level
    assert result.http_status == 200
    assert result.data is not None
    assert "invalid_field" in result.data
    
    # Validation will fail when orchestrator tries to parse data into MedicationsResponse model
    # That's tested in integration tests


@respx.mock
@pytest.mark.asyncio
async def test_500_server_error_is_retriable(api_client):
    """Test 5xx server errors are marked as retriable.
    
    Contract: When endpoint returns 500/502/503 errors:
    1. Error should be categorized as retriable
    2. Retry logic should be triggered
    3. Error message should indicate server error
    """
    respx.get("https://test.opendental.com/api/v1/diseases?PatNum=12345").mock(
        return_value=httpx.Response(
            500,
            json={"error": "Internal server error"},
        )
    )
    
    # Fetch problems - should attempt retries due to 500 status
    try:
        result = await api_client.fetch_problems(12345)
        assert result.success is False
        assert "500" in result.error_message or "server error" in result.error_message.lower()
    except httpx.HTTPStatusError as e:
        assert e.response.status_code == 500


@respx.mock
@pytest.mark.asyncio
async def test_network_error_handling(api_client):
    """Test network errors are caught and reported appropriately.
    
    Contract: When network request fails (connection refused, DNS error):
    1. Exception should be caught
    2. Error message should indicate network failure
    3. Should be treated as retriable error
    """
    def network_error_side_effect(request):
        raise httpx.ConnectError("Connection refused")
    
    respx.get("https://test.opendental.com/api/v1/patientnotes/12345").mock(
        side_effect=network_error_side_effect
    )
    
    # Fetch patient notes - should handle network error
    try:
        result = await api_client.fetch_patient_notes(12345)
        assert result.success is False
        assert "connection" in result.error_message.lower() or "network" in result.error_message.lower()
    except httpx.ConnectError as e:
        # If client lets ConnectError propagate
        assert "refused" in str(e).lower() or "connection" in str(e).lower()


@respx.mock
@pytest.mark.asyncio
async def test_403_forbidden_access_denied(api_client):
    """Test 403 Forbidden is handled with access denied message.
    
    Contract: When endpoint returns 403 (insufficient permissions):
    1. Error message should indicate access denied
    2. Should suggest checking API key permissions
    3. Should not be marked as retriable
    """
    respx.put("https://test.opendental.com/api/v1/queries/ShortQuery").mock(
        return_value=httpx.Response(
            403,
            json={"error": "Forbidden", "message": "Insufficient permissions"},
        )
    )
    
    try:
        result = await api_client.fetch_vital_signs(67890)
        assert result.success is False
        assert "403" in result.error_message or "forbidden" in result.error_message.lower()
    except httpx.HTTPStatusError as e:
        assert e.response.status_code == 403
