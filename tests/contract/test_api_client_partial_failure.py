"""Contract Tests for Partial Failure Scenarios.

Tests API client behavior with mixed success/failure responses.
Verifies individual endpoint failures don't block successful retrievals.
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
async def test_partial_failure_with_503_response(api_client):
    """Test 1 endpoint returning 503, others succeeding.
    
    Contract: When 1 of 6 endpoints returns 503 Service Unavailable,
    the other 5 should succeed and be included in ConsolidatedAuditData.
    The failed endpoint should be recorded in the failures list.
    """
    # Mock 5 successful endpoints
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
    
    # Diseases endpoint fails with 503
    respx.get("https://test.opendental.com/api/v1/diseases?PatNum=12345").mock(
        return_value=httpx.Response(
            503, json={"error": "Service temporarily unavailable"}
        )
    )
    
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
    
    # Execute orchestration equivalent using asyncio.gather
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
    
    # Verify 5 successes, 1 failure
    assert result.successful_count == 5
    assert result.failed_count == 1
    assert result.exit_code() == 2  # Partial failure
    
    # Verify diseases is in failures list
    failure_endpoints = [f["endpoint"] for f in result.failures]
    assert "diseases" in failure_endpoints
    diseases_failure = next(f for f in result.failures if f["endpoint"] == "diseases")
    assert "503" in diseases_failure["error_message"] or "unavailable" in diseases_failure["error_message"].lower()
    
    # Verify other endpoints succeeded
    assert "procedurelogs" in result.success
    assert result.success["procedurelogs"]["PatNum"] == 12345
    assert "allergies" in result.success
    assert "medicationpats" in result.success
    assert "patientnotes" in result.success
    assert "vital_signs" in result.success
