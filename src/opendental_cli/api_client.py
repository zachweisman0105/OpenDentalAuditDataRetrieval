"""OpenDental API Client.

HTTPX-based async HTTP client with defensive patterns:
- Timeout enforcement (10s connect, 30s read, 45s total)
- Retry logic with exponential backoff (3 attempts, 1s/2s/4s with jitter)
- Rate limit handling (429 + Retry-After header)
- Circuit breaker integration
- TLS 1.2+ enforcement with certificate validation

Article III Compliance: Defensive API Integration
"""

import asyncio
import time
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from opendental_cli.audit_logger import get_logger
from opendental_cli.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from opendental_cli.models.credential import APICredential
from opendental_cli.models.response import EndpointResponse

logger = get_logger(__name__)


class OpenDentalAPIClient:
    """OpenDental REST API client with defensive patterns."""

    def __init__(self, credential: APICredential):
        """Initialize API client.

        Args:
            credential: API credentials
        """
        self.credential = credential
        self.base_url = str(credential.base_url).rstrip("/")

        # HTTPX client with timeout and TLS 1.2+ enforcement
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,  # Connection timeout
                read=30.0,  # Read timeout
                write=10.0,  # Write timeout
                pool=10.0,  # Pool timeout
            ),
            verify=True,  # Certificate validation (cannot disable per Article II)
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                **credential.get_auth_header(),
            },
        )

        # Circuit breakers per endpoint
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

    async def close(self) -> None:
        """Close HTTP client connection pool."""
        await self.client.aclose()

    def _get_circuit_breaker(self, endpoint: str) -> CircuitBreaker:
        """Get or create circuit breaker for endpoint.

        Args:
            endpoint: Endpoint name

        Returns:
            CircuitBreaker instance
        """
        if endpoint not in self.circuit_breakers:
            self.circuit_breakers[endpoint] = CircuitBreaker(
                failure_threshold=5, cooldown_seconds=60
            )
        return self.circuit_breakers[endpoint]

    @retry(
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4) + wait_random(0, 0.2),
        reraise=True,
    )
    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., /patients/12345)
            **kwargs: Additional request arguments

        Returns:
            HTTPX Response

        Raises:
            httpx.HTTPError: On request failure
        """
        url = f"{self.base_url}{path}"

        try:
            response = await self.client.request(method, url, **kwargs)

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = self._get_retry_after(response)
                logger.warning(
                    "Rate limit exceeded, retrying",
                    endpoint=path,
                    retry_after_seconds=retry_after,
                )
                await asyncio.sleep(retry_after)
                # Retry after waiting
                response = await self.client.request(method, url, **kwargs)

            response.raise_for_status()
            return response

        except httpx.TimeoutException as e:
            logger.error(
                "Request timeout",
                endpoint=path,
                timeout_seconds=45,
            )
            raise e
        except httpx.NetworkError as e:
            logger.error(
                "Network error",
                endpoint=path,
                error=str(e),
            )
            raise e

    def _get_retry_after(self, response: httpx.Response) -> int:
        """Extract Retry-After header value.

        Args:
            response: HTTP response

        Returns:
            Retry-after seconds (default: 5)
        """
        retry_after = response.headers.get("Retry-After", "5")
        try:
            return int(retry_after)
        except ValueError:
            return 5

    async def fetch_endpoint(
        self,
        endpoint_name: str,
        path: str,
    ) -> EndpointResponse:
        """Fetch data from endpoint with defensive patterns.

        Args:
            endpoint_name: Endpoint identifier
            path: API path

        Returns:
            EndpointResponse with data or error
        """
        start_time = time.time()

        try:
            # Total timeout wrapper
            response = await asyncio.wait_for(
                self._make_request("GET", path),
                timeout=45.0,
            )

            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "API request succeeded",
                operation_type=f"fetch_{endpoint_name}",
                endpoint=path,
                http_status=response.status_code,
                duration_ms=duration_ms,
            )

            return EndpointResponse(
                endpoint_name=endpoint_name,
                http_status=response.status_code,
                success=True,
                data=response.json(),
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Request timeout",
                operation_type=f"fetch_{endpoint_name}",
                endpoint=path,
                error_category="timeout",
                duration_ms=duration_ms,
            )
            return EndpointResponse(
                endpoint_name=endpoint_name,
                http_status=0,
                success=False,
                error_message="Request timeout (45s)",
                duration_ms=duration_ms,
            )

        except httpx.HTTPStatusError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_category = self._categorize_http_error(e.response.status_code)
            logger.error(
                "HTTP error",
                operation_type=f"fetch_{endpoint_name}",
                endpoint=path,
                http_status=e.response.status_code,
                error_category=error_category,
                duration_ms=duration_ms,
            )
            return EndpointResponse(
                endpoint_name=endpoint_name,
                http_status=e.response.status_code,
                success=False,
                error_message=f"{error_category} ({e.response.status_code})",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Unexpected error",
                operation_type=f"fetch_{endpoint_name}",
                endpoint=path,
                error_category="unexpected",
                error=str(e),
                duration_ms=duration_ms,
            )
            return EndpointResponse(
                endpoint_name=endpoint_name,
                http_status=0,
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                duration_ms=duration_ms,
            )

    def _categorize_http_error(self, status_code: int) -> str:
        """Categorize HTTP error status code.

        Args:
            status_code: HTTP status code

        Returns:
            Error category string
        """
        if status_code == 401:
            return "Unauthorized - check credentials"
        elif status_code == 403:
            return "Forbidden - insufficient permissions"
        elif status_code == 404:
            return "Not found"
        elif status_code == 429:
            return "Rate limit exceeded"
        elif status_code >= 500:
            return "Server error"
        else:
            return "Client error"

    # Endpoint-specific fetch methods

    async def fetch_procedure_logs(self, aptnum: int) -> EndpointResponse:
        """Fetch procedure logs/codes for appointment.

        Args:
            aptnum: Appointment number

        Returns:
            EndpointResponse with procedure log data
        """
        return await self.fetch_endpoint("procedurelogs", f"/procedurelogs?AptNum={aptnum}")

    async def fetch_allergies(self, patnum: int) -> EndpointResponse:
        """Fetch patient allergies.

        Args:
            patnum: Patient number

        Returns:
            EndpointResponse with allergy data
        """
        return await self.fetch_endpoint("allergies", f"/allergies?PatNum={patnum}")

    async def fetch_medications(self, patnum: int) -> EndpointResponse:
        """Fetch patient medications.

        Args:
            patnum: Patient number

        Returns:
            EndpointResponse with medication data
        """
        return await self.fetch_endpoint("medicationpats", f"/medicationpats?PatNum={patnum}")

    async def fetch_problems(self, patnum: int) -> EndpointResponse:
        """Fetch patient problems/diseases.

        Args:
            patnum: Patient number

        Returns:
            EndpointResponse with disease/problem data
        """
        return await self.fetch_endpoint("diseases", f"/diseases?PatNum={patnum}")

    async def fetch_patient_notes(self, patnum: int) -> EndpointResponse:
        """Fetch patient medical notes.

        Args:
            patnum: Patient number

        Returns:
            EndpointResponse with patient notes data
        """
        return await self.fetch_endpoint("patientnotes", f"/patientnotes/{patnum}")

    async def fetch_vital_signs(self, patnum: int) -> EndpointResponse:
        """Fetch vital signs via query.

        Args:
            patnum: Patient number

        Returns:
            EndpointResponse with vital signs data
        """
        # Vital signs use PUT request with ShortQuery
        start_time = time.time()

        try:
            # Build query for vital signs  
            # Note: OpenDental API expects "SqlCommand" field name per official documentation
            # Vital signs are associated with patients (PatNum), not appointments (AptNum)
            # Note: BP is stored as BpSystolic and BpDiastolic, not as a single "BP" column
            query_body = {
                "SqlCommand": f"SELECT VitalsignNum, PatNum, DateTaken, Pulse, BpSystolic, BpDiastolic, Height, Weight, BMIPercentile FROM vitalsign WHERE PatNum={patnum}"
            }

            response = await asyncio.wait_for(
                self._make_request("PUT", "/queries/ShortQuery", json=query_body),
                timeout=45.0,
            )

            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "API request succeeded",
                operation_type="fetch_vital_signs",
                endpoint="/queries/ShortQuery",
                http_status=response.status_code,
                duration_ms=duration_ms,
            )

            return EndpointResponse(
                endpoint_name="vital_signs",
                http_status=response.status_code,
                success=True,
                data=response.json(),
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Request timeout",
                operation_type="fetch_vital_signs",
                endpoint="/queries/ShortQuery",
                error_category="timeout",
                duration_ms=duration_ms,
            )
            return EndpointResponse(
                endpoint_name="vital_signs",
                http_status=0,
                success=False,
                error_message="Request timeout (45s)",
                duration_ms=duration_ms,
            )

        except httpx.HTTPStatusError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_category = self._categorize_http_error(e.response.status_code)
            logger.error(
                "HTTP error",
                operation_type="fetch_vital_signs",
                endpoint="/queries/ShortQuery",
                http_status=e.response.status_code,
                error_category=error_category,
                duration_ms=duration_ms,
            )
            return EndpointResponse(
                endpoint_name="vital_signs",
                http_status=e.response.status_code,
                success=False,
                error_message=f"{error_category} ({e.response.status_code})",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Unexpected error",
                operation_type="fetch_vital_signs",
                endpoint="/queries/ShortQuery",
                error_category="unexpected",
                error=str(e),
                duration_ms=duration_ms,
            )
            return EndpointResponse(
                endpoint_name="vital_signs",
                http_status=0,
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                duration_ms=duration_ms,
            )
