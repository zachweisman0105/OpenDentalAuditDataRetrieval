# Feature Specification: OpenDental Audit Data Retrieval CLI

**Feature Branch**: `001-audit-data-cli`  
**Created**: 2025-11-29  
**Status**: Draft  
**Input**: User description: "CLI tool where the user enters a PatNum & an AptNum and a certain list of API endpoints are used to get specific JSON data required for audits"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Basic Audit Data Retrieval (Priority: P1)

An auditor needs to retrieve all relevant OpenDental data for a specific patient appointment. They launch the CLI tool, provide a Patient Number (PatNum) and Appointment Number (AptNum), and receive a consolidated JSON file containing data from multiple OpenDental API endpoints required for compliance audits.

**Why this priority**: This is the core MVP functionality. Without the ability to retrieve audit data for a specific patient-appointment pair, the tool has no value. All other features depend on this foundation.

**Independent Test**: Can be fully tested by running the CLI with valid PatNum and AptNum values against mocked API responses, verifying that JSON output contains data from all required endpoints with correct structure.

**Acceptance Scenarios**:

1. **Given** valid credentials are configured in keyring, **When** user runs `opendental-cli --patnum 12345 --aptnum 67890`, **Then** system fetches data from all configured endpoints and outputs consolidated JSON to stdout
2. **Given** valid credentials and output file specified, **When** user runs `opendental-cli --patnum 12345 --aptnum 67890 --output audit_data.json`, **Then** system writes consolidated JSON to specified file with restrictive permissions (600)
3. **Given** API returns data successfully, **When** retrieval completes, **Then** JSON output contains sections for each endpoint (patient, appointment, treatment_history, billing_records, etc.) with proper nesting
4. **Given** user has not configured credentials, **When** user runs tool, **Then** system displays clear error message directing user to run `opendental-cli config set-credentials` and exits with code 1

---

### User Story 2 - PHI Redacted Output (Priority: P2)

An auditor needs to share API response structure and error scenarios with technical support without exposing actual patient data. They use the `--redact-phi` flag to generate JSON output where sensitive fields are replaced with `[REDACTED]` placeholders while preserving data structure for debugging.

**Why this priority**: HIPAA compliance requires the ability to demonstrate system behavior without exposing PHI. This enables safe debugging, documentation, and technical support workflows.

**Independent Test**: Can be fully tested by running CLI with `--redact-phi` flag and verifying that output JSON has `[REDACTED]` in place of patient names, dates of birth, appointment dates, provider names, and other PHI while maintaining valid JSON structure.

**Acceptance Scenarios**:

1. **Given** valid data retrieved, **When** user runs `opendental-cli --patnum 12345 --aptnum 67890 --redact-phi`, **Then** output JSON contains `[REDACTED]` for all PHI fields (patient_name, dob, ssn, appointment_date, provider_name) but preserves structure
2. **Given** redacted output requested, **When** reviewing JSON structure, **Then** field names and data types remain intact to enable schema validation and debugging

---

### User Story 3 - Partial Failure Recovery (Priority: P3)

An auditor runs the tool but one of the API endpoints is temporarily unavailable (e.g., billing service down). The tool continues fetching data from remaining endpoints and returns partial results with explicit annotations about which endpoints failed, allowing the auditor to proceed with available data and retry only failed endpoints later.

**Why this priority**: Healthcare APIs can experience partial outages. Failing completely when one endpoint is down wastes time and reduces tool reliability. This priority comes after core functionality and PHI redaction because it's an enhancement to error handling.

**Independent Test**: Can be fully tested by mocking one endpoint to return 503 error while others succeed, verifying tool continues execution, returns partial data, and clearly indicates which endpoint failed in output structure.

**Acceptance Scenarios**:

1. **Given** patient endpoint succeeds but appointment endpoint returns 503, **When** tool executes, **Then** output contains `{"success": {"patient": {...}}, "failures": [{"endpoint": "appointment", "error": "Service unavailable (503)"}]}` and exits with code 2 (partial failure)
2. **Given** multiple endpoints fail, **When** tool completes, **Then** all successful data is returned and all failures are listed with endpoint names and error messages
3. **Given** all endpoints fail, **When** tool completes, **Then** output contains only failures section and exits with code 1 (complete failure)

---

### User Story 4 - Credential Management (Priority: P2)

A user needs to configure OpenDental API credentials securely for the first time. They run `opendental-cli config set-credentials` which prompts for API key and base URL, then stores credentials in the OS keyring (Windows Credential Manager, macOS Keychain, or Linux Secret Service) with proper encryption.

**Why this priority**: Secure credential storage is foundational for HIPAA compliance. While not part of the audit data retrieval workflow itself, it's required before any data can be fetched. Ranked P2 because it's essential but only needs to be done once per environment.

**Independent Test**: Can be fully tested by running config command, verifying credentials are stored in keyring under service name `opendental-audit-cli`, and confirming subsequent CLI runs can retrieve credentials without prompting.

**Acceptance Scenarios**:

1. **Given** no credentials exist, **When** user runs `opendental-cli config set-credentials`, **Then** system prompts for API key and base URL, validates format, stores in keyring, and confirms success
2. **Given** credentials already exist, **When** user runs config command, **Then** system prompts to confirm overwrite before updating keyring
3. **Given** keyring unavailable, **When** config command runs, **Then** system displays error explaining keyring requirement and suggests fallback to environment variables with security warning

### Edge Cases

- **Invalid PatNum/AptNum**: What happens when user provides non-numeric, negative, or zero values? System must validate inputs and reject with clear error message.
- **Non-existent PatNum/AptNum**: What happens when API returns 404 for patient or appointment? System must distinguish between "not found" vs "access denied" and report accordingly.
- **API timeout during retrieval**: What happens if one endpoint takes longer than 45 seconds? System must honor timeout, mark endpoint as failed, continue with others.
- **Malformed API response**: What happens when API returns invalid JSON or missing required fields? System must validate schema, log error details (non-PHI), and treat as endpoint failure.
- **Credentials expired/revoked**: What happens when API returns 401 during execution? System must detect authentication failure, display clear error, and instruct user to update credentials.
- **Concurrent executions**: What happens if user runs multiple CLI instances simultaneously? Each instance operates independently with no shared state.
- **Very large API responses**: What happens when appointment has extensive treatment history (e.g., 10MB response)? System must handle large payloads up to reasonable limits (document max response size, e.g., 50MB).
- **Unicode in patient names**: What happens when patient name contains non-ASCII characters? System must preserve UTF-8 encoding throughout pipeline.
- **Output file already exists**: What happens when user specifies `--output` for existing file? System must prompt to confirm overwrite or use `--force` flag to skip confirmation.
- **Insufficient file system permissions**: What happens when user lacks write permissions for output directory? System must detect permission error before API calls and fail fast with clear message.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST accept PatNum and AptNum as required command-line arguments, validating both are positive integers
- **FR-002**: System MUST retrieve OpenDental API credentials from OS keyring (primary) or environment variables (fallback)
- **FR-003**: System MUST query multiple OpenDental API endpoints (patient details, appointment details, treatment history, billing records, insurance claims, clinical notes) using provided PatNum and AptNum
- **FR-004**: System MUST implement timeout (45s), retry logic (3 attempts with exponential backoff), and rate limit handling per Article III of constitution
- **FR-005**: System MUST consolidate responses from all endpoints into single JSON structure with clear endpoint labeling
- **FR-006**: System MUST output consolidated JSON to stdout by default or to file specified via `--output` flag
- **FR-007**: System MUST sanitize all logging and error output per Article II to prevent PHI leakage (no patient names, DOBs, SSNs, dates, or provider names in logs)
- **FR-008**: System MUST support `--redact-phi` flag to replace sensitive fields with `[REDACTED]` in output JSON while preserving structure
- **FR-009**: System MUST handle partial failures by continuing execution when one endpoint fails, returning successful data plus failure annotations
- **FR-010**: System MUST generate audit log entry for each API call containing timestamp (UTC), operation type, endpoint, success/failure status, but NO PHI data
- **FR-011**: System MUST create output files with restrictive permissions (600 on Unix, equivalent ACL on Windows)
- **FR-012**: System MUST use TLS 1.2+ for all API communication with certificate validation enabled
- **FR-013**: System MUST provide `config set-credentials` subcommand to store API key and base URL in OS keyring under service name `opendental-audit-cli`
- **FR-014**: System MUST validate API responses against expected schema, treating missing required fields as errors
- **FR-015**: System MUST exit with appropriate status codes: 0 (success), 1 (failure), 2 (partial success)

### Key Entities

- **AuditDataRequest**: Represents a user's request for audit data, containing PatNum, AptNum, output destination, and redaction preference
- **APICredential**: Represents OpenDental API authentication, containing API key and base URL (stored in keyring, never in memory longer than needed)
- **EndpointResponse**: Represents response from single API endpoint, containing endpoint name, HTTP status, raw data, timestamp, and error details if failed
- **ConsolidatedAuditData**: Represents final output structure, containing successful endpoint responses organized by category (patient, appointment, treatment, billing) plus failure annotations
- **AuditLogEntry**: Represents single log record for audit trail, containing timestamp (UTC), operation type, endpoint name, status, duration, NO PHI

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Users can retrieve audit data for a patient-appointment pair in under 60 seconds (assuming normal API response times)
- **SC-002**: System successfully handles API failures for individual endpoints without losing data from successful endpoints (100% partial failure isolation)
- **SC-003**: Zero PHI leakage in logs, error messages, or console output when `--redact-phi` flag is used (verified through comprehensive log analysis)
- **SC-004**: Credentials are stored using OS-native keyring with AES-256-GCM encryption on all supported platforms (Windows, macOS, Linux)
- **SC-005**: 100% of automated tests run without making actual API calls (fully offline test suite)
- **SC-006**: Tool executes successfully in fully offline environment when using mocked API responses (enables local development)
- **SC-007**: Users can complete initial credential setup in under 3 minutes with clear instructions
- **SC-008**: System maintains 90%+ test coverage for business logic, 100% for security-critical code (credential handling, PHI sanitization)

## Assumptions

- **OpenDental API access**: User has valid OpenDental API credentials with read access to patient, appointment, treatment, billing, and clinical data
- **API endpoints**: OpenDental provides RESTful API endpoints for patient data, appointment data, treatment history, billing records, insurance claims, and clinical notes (specific endpoints to be determined during research phase)
- **Network connectivity**: User has reliable internet connection to OpenDental API server
- **OS platform**: Tool runs on Windows 10+, macOS 10.15+, or Linux distributions with keyring support (GNOME Keyring, KWallet, or Secret Service)
- **Authentication method**: OpenDental API uses API key-based authentication (Bearer token or similar)
- **Response format**: All API endpoints return JSON responses
- **Rate limits**: OpenDental API has reasonable rate limits allowing sequential endpoint queries for single patient-appointment pair
- **Data volume**: Single patient-appointment audit data retrieval results in <50MB total across all endpoints
- **User permissions**: User running CLI has file system write permissions in their working directory
- **Single environment**: Initial version targets single OpenDental environment (production OR staging, not simultaneous multi-environment support)
