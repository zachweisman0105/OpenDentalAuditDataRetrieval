# Feature Specification: OpenDental API Endpoint Authorization & Format Fix

**Feature Branch**: `002-endpoint-auth-fix`  
**Created**: 2025-12-02  
**Status**: Draft  
**Input**: User reports error when retrieving patient data. Need to verify API endpoint authorization headers and request/response formats match OpenDental API contract.

## Problem Statement

The CLI tool is encountering errors when attempting to retrieve audit data for patients. The root cause is suspected to be one or both of:
1. **Authentication/Authorization Issue**: API requests may not be sending authentication headers correctly or in the expected format
2. **Endpoint Format Issue**: Request URLs, HTTP methods, query parameters, or path parameters may not match OpenDental API contract specifications

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Diagnose API Communication Failures (Priority: P1)

A developer needs to identify why the CLI tool fails to retrieve patient data. They review audit logs, API contract documentation, and current implementation to identify mismatches in authentication headers, endpoint paths, HTTP methods, or request/response formats.

**Why this priority**: Cannot fix the issue without first understanding the root cause. This is diagnostic work that blocks all other functionality.

**Independent Test**: Review code and documentation, create test script that attempts each endpoint with proper authentication, verify actual API responses match documented contract.

**Acceptance Scenarios**:

1. **Given** API contract specifies authentication headers, **When** reviewing api_client.py implementation, **Then** code sends DeveloperKey and CustomerKey headers exactly as specified in contract
2. **Given** API contract specifies endpoint paths and HTTP methods, **When** reviewing fetch_* methods, **Then** all endpoints use correct HTTP method (GET vs PUT), correct path format (query params vs path params), and correct parameter names
3. **Given** test credentials configured, **When** running diagnostic test against actual API, **Then** error messages clearly indicate whether issue is authentication (401/403) or format (400/404)

---

### User Story 2 - Fix Authentication Header Format (Priority: P1)

If authentication is the issue, developer updates the credential model and API client to send authentication headers in the exact format expected by OpenDental API (custom headers: DeveloperKey and CustomerKey).

**Why this priority**: If authentication is broken, no endpoints will work. Must be fixed before testing endpoint formats.

**Independent Test**: Configure valid credentials, make test request to known-working endpoint, verify 200 response instead of 401/403.

**Acceptance Scenarios**:

1. **Given** valid Developer Key and Customer Key, **When** API client makes request, **Then** request includes headers "DeveloperKey: {key}" and "CustomerKey: {key}" exactly as specified
2. **Given** credentials configured in keyring, **When** retrieving via get_credentials(), **Then** both developer_key and customer_key are loaded and passed to API client
3. **Given** corrected authentication, **When** making test request, **Then** receive 200 OK instead of 401 Unauthorized

---

### User Story 3 - Fix Endpoint Request Formats (Priority: P2)

Once authentication works, developer verifies and fixes any endpoint-specific issues with HTTP methods, URL paths, query parameters, or request bodies to match API contract exactly.

**Why this priority**: Individual endpoints may have format issues even if authentication works. Must verify each endpoint's request format.

**Independent Test**: With working authentication, test each of 6 endpoints individually, verify responses match contract specifications.

**Acceptance Scenarios**:

1. **Given** /patientnotes endpoint requires PatNum in path, **When** calling fetch_patient_notes(12345), **Then** request URL is "/patientnotes/12345" not "/patientnotes?PatNum=12345"
2. **Given** /queries/ShortQuery requires PUT method, **When** calling fetch_vital_signs(), **Then** uses PUT not GET
3. **Given** /queries/ShortQuery requires "Query" key in JSON body, **When** calling fetch_vital_signs(), **Then** request body contains {"Query": "SELECT..."} with capital Q
4. **Given** all endpoints corrected, **When** running full audit retrieval for PatNum+AptNum, **Then** all 6 endpoints return 200 OK with valid data

---

### User Story 4 - Update Tests and Documentation (Priority: P3)

After fixes are implemented, developer updates test fixtures, unit tests, integration tests, and API contract documentation to reflect correct implementation.

**Why this priority**: Ensures future changes don't break authentication/endpoints again, and documents working implementation for other developers.

**Independent Test**: All tests pass with corrected implementation, documentation accurately reflects working code.

**Acceptance Scenarios**:

1. **Given** authentication fix implemented, **When** running unit tests for credential_manager, **Then** tests verify both developer_key and customer_key are stored/retrieved
2. **Given** endpoint fixes implemented, **When** running contract tests, **Then** mock responses match actual API contract specifications
3. **Given** all fixes complete, **When** reviewing contracts/opendental-api.md, **Then** document accurately describes authentication headers and endpoint formats used in implementation

### Edge Cases

- **Expired credentials**: API returns 401 even with correct header format - must distinguish from wrong header format
- **Missing permissions**: API returns 403 even with valid credentials - must provide clear error message
- **Typos in header names**: "DeveloperKey" vs "Developer-Key" vs "developerKey" - must match API exactly
- **Case sensitivity**: Query parameter names may be case-sensitive (PatNum vs patnum)
- **Trailing slashes**: Base URL with/without trailing slash may affect path construction
- **Query parameter encoding**: Special characters in query values must be URL-encoded
- **PUT vs POST**: Vital signs endpoint uses PUT, not POST - must verify method

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST send authentication via custom HTTP headers "DeveloperKey" and "CustomerKey" exactly as specified in OpenDental API contract
- **FR-002**: System MUST store both developer_key and customer_key in credential model and keyring (not just single api_key)
- **FR-003**: System MUST construct endpoint URLs matching contract specifications: query parameters for most endpoints, path parameters for patientnotes
- **FR-004**: System MUST use PUT method for /queries/ShortQuery endpoint, GET for all others
- **FR-005**: System MUST send JSON body with "Query" key (capital Q) for vital signs ShortQuery request
- **FR-006**: System MUST handle 401 Unauthorized responses by displaying credential configuration instructions
- **FR-007**: System MUST handle 403 Forbidden responses by displaying permission error message
- **FR-008**: System MUST provide diagnostic error messages that distinguish between authentication failures (401/403) and format errors (400/404)
- **FR-009**: System MUST validate all six endpoints work with corrected implementation: procedurelogs, allergies, medicationpats, diseases, patientnotes, vital_signs
- **FR-010**: System MUST update all test fixtures and contract tests to reflect correct authentication and endpoint formats

### Key Entities

- **APICredential**: Must include both `developer_key` and `customer_key` fields (not just single `api_key`)
- **OpenDentalAPIClient**: Must construct headers dict with both DeveloperKey and CustomerKey
- **EndpointResponse**: Must capture authentication errors separately from format errors for diagnostic purposes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 6 API endpoints return 200 OK responses when called with valid test credentials
- **SC-002**: Authentication headers in actual HTTP requests match contract specification exactly (verified via network capture or API logs)
- **SC-003**: Endpoint request formats (method, path, params) match contract specification for all 6 endpoints
- **SC-004**: Users receive clear error message distinguishing authentication issues from endpoint format issues
- **SC-005**: 100% of contract tests pass with corrected implementation
- **SC-006**: Integration tests successfully retrieve audit data for test patient without errors

## Assumptions

- **API contract documentation is accurate**: The contracts/opendental-api.md file correctly documents OpenDental API requirements
- **Test credentials available**: Valid developer_key and customer_key can be obtained for testing
- **API is operational**: OpenDental API server is available and not experiencing outages during testing
- **Current implementation has bugs**: Either authentication headers or endpoint formats (or both) are incorrect in current code
- **Backward compatibility not required**: This is a bug fix that may require breaking changes to credential storage format if developer_key and customer_key need to be stored separately
