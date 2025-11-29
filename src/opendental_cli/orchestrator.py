"""Orchestrator for Multi-Endpoint Data Retrieval.

Coordinates fetching data from all OpenDental API endpoints.
Handles partial failures and consolidates results.

Article III Compliance: Partial Failure Isolation
"""

import asyncio
from datetime import datetime, timezone

from opendental_cli.api_client import OpenDentalAPIClient
from opendental_cli.audit_logger import get_logger
from opendental_cli.models.credential import APICredential
from opendental_cli.models.request import AuditDataRequest
from opendental_cli.models.response import ConsolidatedAuditData, EndpointResponse

logger = get_logger(__name__)


async def orchestrate_retrieval(
    request: AuditDataRequest,
    credential: APICredential,
) -> ConsolidatedAuditData:
    """Orchestrate data retrieval from all endpoints.

    Uses asyncio.gather() to fetch from 6 endpoints concurrently:
    - procedurelogs (procedure codes)
    - allergies (patient allergies)
    - medicationpats (medications)
    - diseases (problems)
    - patientnotes (medical info)
    - vital_signs (queries)

    Args:
        request: Audit data request
        credential: API credentials

    Returns:
        ConsolidatedAuditData with results from all endpoints
    """
    logger.info(
        "Starting audit data retrieval",
        patnum=request.patnum,
        aptnum=request.aptnum,
    )

    # Create API client
    client = OpenDentalAPIClient(credential)

    try:
        # Fetch all endpoints concurrently
        results = await asyncio.gather(
            client.fetch_procedure_logs(request.aptnum),
            client.fetch_allergies(request.patnum),
            client.fetch_medications(request.patnum),
            client.fetch_problems(request.patnum),
            client.fetch_patient_notes(request.patnum),
            client.fetch_vital_signs(request.aptnum),
            return_exceptions=True,
        )

        # Segregate successes and failures
        success_dict = {}
        failures = []

        for result in results:
            if isinstance(result, Exception):
                logger.error("Unexpected exception", error=str(result))
                failures.append(
                    EndpointResponse(
                        endpoint_name="unknown",
                        http_status=0,
                        success=False,
                        error_message=f"Exception: {str(result)}",
                        duration_ms=0.0,
                    )
                )
                continue

            if not isinstance(result, EndpointResponse):
                continue

            if result.success:
                success_dict[result.endpoint_name] = result.data
                logger.info(
                    "Endpoint succeeded",
                    endpoint=result.endpoint_name,
                    http_status=result.http_status,
                )
            else:
                failures.append({
                    "endpoint": result.endpoint_name,
                    "http_status": str(result.http_status),
                    "error_message": result.error_message or "Unknown error",
                })
                logger.warning(
                    "Endpoint failed",
                    endpoint=result.endpoint_name,
                    error=result.error_message,
                )

    finally:
        await client.close()

    consolidated = ConsolidatedAuditData(
        request=request,
        success=success_dict,
        failures=failures,
        total_endpoints=6,
        successful_count=len(success_dict),
        failed_count=len(failures),
        retrieval_timestamp=datetime.now(timezone.utc),
    )

    logger.info(
        "Retrieval complete",
        successful_count=len(success_dict),
        failed_count=len(failures),
        exit_code=consolidated.exit_code(),
    )

    return consolidated
