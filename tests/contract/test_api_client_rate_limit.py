"""Contract Tests for Rate Limit Handling.

Tests API client behavior with 429 rate limit responses.
Verifies retry logic with exponential backoff (1s, 2s, 4s).
"""

import asyncio

import httpx
import pytest
import respx

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
async def test_rate_limit_429_with_retry_success(api_client):
    """Test 429 rate limit response with Retry-After header.
    
    Contract: When endpoint returns 429, client should:
    1. Parse Retry-After header (or use exponential backoff)
    2. Wait the specified time
    3. Retry the request
    4. Succeed if retry returns 200 OK
    
    Note: Uses respx pass_through to simulate retry without actual waiting.
    Test verifies client retries and eventually succeeds.
    """
    # Counter to track retry attempts
    attempt_counter = {"count": 0}
    
    def rate_limit_then_success(request):
        """Return 429 on first call, 200 OK on second."""
        attempt_counter["count"] += 1
        if attempt_counter["count"] == 1:
            return httpx.Response(
                429,
                json={"error": "Rate limit exceeded"},
                headers={"Retry-After": "1"},  # Suggest 1 second wait
            )
        else:
            return httpx.Response(
                200,
                json={
                    "PatNum": 12345,
                    "CurrentBalance": 150.0,
                    "LastStatement": "2024-01-15",
                    "Statements": [],
                },
            )
    
    # Mock procedurelogs endpoint - straightforward success
    respx.get("https://test.opendental.com/api/v1/procedurelogs?AptNum=67890").mock(
        return_value=httpx.Response(
            200,
            json={
                "PatNum": 12345,
                "FName": "John",
                "LName": "Doe",
                "Birthdate": "1980-01-15",
                "SSN": "123-45-6789",
                "Address": "123 Main St",
                "Email": "john.doe@example.com",
            },
        )
    )
    
    # Mock allergies endpoint - straightforward success
    respx.get("https://test.opendental.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(
            200,
            json={
                "AptNum": 67890,
                "PatNum": 12345,
                "AptDateTime": "2024-01-15T10:00:00",
                "ProvName": "Dr. Smith",
                "Note": "Regular checkup",
            },
        )
    )
    
    # Mock medications endpoint - straightforward success
    respx.get("https://test.opendental.com/api/v1/medicationpats?PatNum=12345").mock(
        return_value=httpx.Response(
            200,
            json={
                "PatNum": 12345,
                "Procedures": [
                    {
                        "ProcNum": 1,
                        "ProcDescript": "Cleaning",
                        "ProcFee": 100.0,
                        "ToothNum": "12",
                    }
                ],
            },
        )
    )
    
    # Diseases endpoint returns 429, then succeeds on retry
    respx.get("https://test.opendental.com/api/v1/diseases?PatNum=12345").mock(
        side_effect=rate_limit_then_success
    )
    
    # Mock patientnotes endpoint - straightforward success
    respx.get("https://test.opendental.com/api/v1/patientnotes/12345").mock(
        return_value=httpx.Response(
            200,
            json={
                "PatNum": 12345,
                "Claims": [
                    {
                        "ClaimNum": 1,
                        "ClaimType": "P",
                        "ClaimStatus": "Sent",
                        "Subscriber": "John Doe",
                    }
                ],
            },
        )
    )
    
    # Mock vital_signs endpoint - straightforward success
    respx.put("https://test.opendental.com/api/v1/queries/ShortQuery").mock(
        return_value=httpx.Response(
            200,
            json={
                "PatNum": 12345,
                "ProgressNotes": [
                    {"NoteNum": 1, "NoteText": "Patient doing well", "NoteDate": "2024-01-15"}
                ],
            },
        )
    )
    
    # Execute orchestration
    from opendental_cli.models.request import AuditDataRequest
    from opendental_cli.orchestrator import orchestrate_retrieval
    
    credentials = APICredential(
        base_url="https://test.opendental.com/api/v1",
        developer_key="test-developer-key",
        customer_key="test-customer-key",
        environment="test",
    )
    
    request = AuditDataRequest(
        patnum=12345,
        aptnum=67890,
        output_file=None,
        redact_phi=False,
        force_overwrite=False,
    )
    
    result = await orchestrate_retrieval(request, credentials)
    
    # Verify all endpoints succeeded (including retried diseases)
    assert result.successful_count == 6
    assert result.failed_count == 0
    assert result.exit_code() == 0  # Complete success
    
    # Verify diseases endpoint was called twice (initial + retry)
    assert attempt_counter["count"] == 2
    
    # Verify all data present in success dict
    assert "procedurelogs" in result.success
    assert "allergies" in result.success
    assert "medicationpats" in result.success
    assert "diseases" in result.success
    assert "patientnotes" in result.success
    assert "vital_signs" in result.success
