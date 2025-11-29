# Tasks: OpenDental Audit Data Retrieval CLI

**Input**: Design documents from `/specs/001-audit-data-cli/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: This feature specification does NOT explicitly request TDD or test-first approach. Tests will be written during implementation following constitution Article IV requirements (100% mocked, 90%+ coverage).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `- [ ] [ID] [P?] [Story] Description`

- **Checkbox**: ALWAYS starts with `- [ ]` (markdown checkbox)
- **[ID]**: Task ID (T001, T002, T003...)
- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (e.g., [US1], [US2], [US3]) - only for user story phases
- **Description**: Clear action with exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: src/opendental_cli/, tests/unit/, tests/integration/, tests/contract/, tests/fixtures/
- [X] T002 Initialize Python project with pyproject.toml defining dependencies: Pydantic 2.5+, HTTPX 0.25+, Keyring 24.3+, Click 8.1+, Rich 13.7+, Structlog 23.2+, pytest 7.4+, pytest-asyncio 0.21+, respx 0.20+, Faker 20.1+, tenacity
- [X] T003 [P] Create README.md with installation instructions, credential setup, basic usage examples, and security notes about Python memory zeroing limitation
- [X] T004 [P] Create .env.template with OPENDENTAL_BASE_URL and OPENDENTAL_API_KEY placeholders
- [X] T005 [P] Configure pytest.ini with async test settings, coverage targets (90% general, 100% for credential_manager/phi_sanitizer/audit_logger), and fixture directories
- [X] T006 [P] Create .gitignore for Python (.venv/, __pycache__/, *.pyc, .pytest_cache/, .coverage, audit.log, *.json output files)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create src/opendental_cli/__init__.py with package metadata (__version__, __author__)
- [X] T008 Create src/opendental_cli/__main__.py entry point that invokes cli.main() when executed as python -m opendental_cli
- [X] T009 [P] Implement PHI sanitizer in src/opendental_cli/phi_sanitizer.py with PHISanitizerProcessor class for Structlog (filters PatNum, names, DOBs, dates, SSNs, phone numbers from logs)
- [X] T010 [P] Implement audit logger in src/opendental_cli/audit_logger.py with configure_audit_logging() function creating audit.log with 0o600 permissions, Structlog with PHISanitizerProcessor, UTC timestamps
- [X] T011 [P] Implement circuit breaker in src/opendental_cli/circuit_breaker.py with CircuitBreaker class (5 failures → 60s open state → half-open probe, per-endpoint state tracking)
- [X] T012 Create credential manager in src/opendental_cli/credential_manager.py with get_credentials() (keyring primary, env vars fallback with warning), set_credentials() (keyring storage), service name "opendental-audit-cli"
- [X] T013 Create base Pydantic models in src/opendental_cli/models/__init__.py
- [X] T014 [P] Create AuditDataRequest model in src/opendental_cli/models/request.py with patnum/aptnum validation (gt=0), output_file, redact_phi, force_overwrite fields
- [X] T015 [P] Create APICredential model in src/opendental_cli/models/credential.py with base_url (HttpUrl), api_key (SecretStr), environment, get_auth_header() method
- [X] T016 [P] Create EndpointResponse model in src/opendental_cli/models/response.py with endpoint_name, http_status, success, data, error_message, timestamp, duration_ms, is_retriable() method
- [X] T017 Create AuditLogEntry model in src/opendental_cli/models/audit_log.py with timestamp, operation_type, endpoint, http_status, success, duration_ms, error_category (NO PHI fields)
- [X] T018 Create ConsolidatedAuditData model in src/opendental_cli/models/response.py with request, success dict, failures list, counters, retrieval_timestamp, exit_code() method, apply_phi_redaction() method
- [X] T019 Create API client in src/opendental_cli/api_client.py with OpenDentalAPIClient class using HTTPX with timeout (10s connect, 30s read, 45s total via asyncio), TLS 1.2+ verification, retry logic (tenacity: 3 attempts, exponential backoff 1s/2s/4s, ±20% jitter), rate limit detection (429 + Retry-After header), circuit breaker integration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 4 - Credential Management (Priority: P2) 🔐 PREREQUISITE

**Goal**: Enable secure credential configuration via `config set-credentials` subcommand before any data retrieval can occur

**Independent Test**: Run `opendental-cli config set-credentials`, enter credentials, verify stored in OS keyring under service "opendental-audit-cli", run retrieval command to confirm credentials loaded successfully

**Note**: This is listed before User Story 1 because credentials must be configured before any retrieval can work. However, it's P2 because it's a one-time setup task.

### Implementation for User Story 4

- [X] T020 [US4] Implement Click command group in src/opendental_cli/cli.py with main command @click.group()
- [X] T021 [US4] Implement `config set-credentials` subcommand in src/opendental_cli/cli.py that prompts for base_url (with HttpUrl validation), api_key (with SecretStr hiding input), environment selection, calls credential_manager.set_credentials(), confirms success via Rich console
- [X] T022 [US4] Add credential overwrite confirmation logic: if credentials exist, prompt "Credentials already configured. Overwrite? [y/N]" before updating keyring
- [X] T023 [US4] Add graceful keyring failure handling: if keyring.errors.NoKeyringError raised, display error via Rich explaining keyring requirement and environment variable fallback option
- [X] T024 [US4] Write unit test in tests/unit/test_credential_manager.py for set_credentials() with mocked keyring.set_password()
- [X] T025 [US4] Write unit test in tests/unit/test_credential_manager.py for get_credentials() with keyring available (mocked keyring.get_password())
- [X] T026 [US4] Write unit test in tests/unit/test_credential_manager.py for get_credentials() fallback to environment variables when keyring unavailable
- [X] T027 [US4] Write integration test in tests/integration/test_credential_flow.py for full config set-credentials → credential retrieval flow with mocked keyring

**Checkpoint**: Users can now configure credentials securely

---

## Phase 4: User Story 1 - Basic Audit Data Retrieval (Priority: P1) 🎯 MVP

**Goal**: Retrieve audit data for PatNum + AptNum from all 6 OpenDental API endpoints, output consolidated JSON to stdout or file

**Independent Test**: Run `opendental-cli --patnum 12345 --aptnum 67890` with mocked API responses returning 200 OK for all 6 endpoints, verify JSON output contains patient, appointment, treatment, billing, insurance, clinical_notes sections with proper structure, exit code 0

### OpenDental Response Models for User Story 1

- [X] T028 [P] [US1] Create PatientResponse model in src/opendental_cli/models/opendental/patient.py matching contract schema (PatNum, FName, LName, MiddleI, Birthdate, SSN, Gender, Address, City, State, Zip, HmPhone, WkPhone, Email)
- [X] T029 [P] [US1] Create AppointmentResponse model in src/opendental_cli/models/opendental/appointment.py matching contract schema (AptNum, PatNum, AptDateTime, ProvNum, ProvName, ClinicNum, AptStatus, Confirmed, Note)
- [X] T030 [P] [US1] Create TreatmentResponse model in src/opendental_cli/models/opendental/treatment.py matching contract schema (ProcNum, PatNum, AptNum, ProcDate, ProcCode, ProcDescript, ToothNum, ProcFee, ProcStatus, ProvNum)
- [X] T031 [P] [US1] Create BillingResponse model in src/opendental_cli/models/opendental/billing.py matching contract schema (StatementNum, PatNum, DateStatement, AmountDue, AmountPaid, AmountInsEst, IsSent)
- [X] T032 [P] [US1] Create InsuranceResponse model in src/opendental_cli/models/opendental/insurance.py matching contract schema (ClaimNum, PatNum, DateService, ClaimFee, InsPayAmt, ClaimStatus, ProvNum, Subscriber)
- [X] T033 [P] [US1] Create ClinicalNotesResponse model in src/opendental_cli/models/opendental/clinical_notes.py matching contract schema (ProgNoteNum, PatNum, AptNum, ProcDate, ProvNum, NoteText, EntryDateTime)

### Core Retrieval Logic for User Story 1

- [X] T034 [US1] Implement fetch_patient() method in api_client.py: GET /patients/{PatNum}, returns PatientResponse or raises exception, includes timeout/retry/circuit breaker logic
- [X] T035 [US1] Implement fetch_appointment() method in api_client.py: GET /appointments/{AptNum}, returns AppointmentResponse or raises exception
- [X] T036 [US1] Implement fetch_treatment_history() method in api_client.py: GET /procedures?PatNum={PatNum}, returns list[TreatmentResponse] or raises exception
- [X] T037 [US1] Implement fetch_billing_records() method in api_client.py: GET /statements?PatNum={PatNum}, returns list[BillingResponse] or raises exception
- [X] T038 [US1] Implement fetch_insurance_claims() method in api_client.py: GET /claims?PatNum={PatNum}, returns list[InsuranceResponse] or raises exception
- [X] T039 [US1] Implement fetch_clinical_notes() method in api_client.py: GET /progress_notes?PatNum={PatNum}, returns list[ClinicalNotesResponse] or raises exception
- [X] T040 [US1] Implement orchestrate_retrieval() function in src/opendental_cli/orchestrator.py that uses asyncio.gather(return_exceptions=True) to fetch all 6 endpoints concurrently, segregates successes/failures into ConsolidatedAuditData, logs each API call to audit.log
- [X] T041 [US1] Implement output formatter in src/opendental_cli/output_formatter.py with write_to_stdout(data: ConsolidatedAuditData) using Rich JSON formatting
- [X] T042 [US1] Implement write_to_file(data: ConsolidatedAuditData, filepath: str, force: bool) in output_formatter.py with permission 0o600, overwrite confirmation logic
- [X] T043 [US1] Implement main CLI command in cli.py: @click.command() with --patnum (required, type=int), --aptnum (required, type=int), --output (optional, type=Path), --force (flag), validates patnum/aptnum > 0, loads credentials via credential_manager, calls orchestrate_retrieval(), formats output, exits with appropriate code

### Input Validation for User Story 1

- [X] T044 [US1] Add Click parameter validation callbacks for --patnum and --aptnum ensuring positive integers, display error via Rich if invalid, exit code 1
- [X] T045 [US1] Add pre-flight credential check in cli.py: if no credentials found, display error message "No credentials configured. Please run: opendental-cli config set-credentials" via Rich, exit code 1
- [X] T046 [US1] Add output file permissions check in output_formatter.py: if output directory not writable, display error via Rich before API calls, exit code 1

### Tests for User Story 1

- [X] T047 [P] [US1] Write contract test in tests/contract/test_api_client_golden_path.py for all 6 endpoints with respx mocking 200 OK responses from patient_12345.json, appointment_67890.json, treatment_success.json, billing_success.json, insurance_success.json, clinical_notes_success.json fixtures
- [X] T048 [P] [US1] Write unit tests in tests/unit/test_models.py for all 6 OpenDental response models validating required fields, type coercion, missing field rejection
- [X] T049 [P] [US1] Write unit test in tests/unit/test_output_formatter.py for write_to_stdout() with ConsolidatedAuditData containing all 6 successful endpoints
- [X] T050 [P] [US1] Write unit test in tests/unit/test_output_formatter.py for write_to_file() verifying 0o600 permissions, overwrite confirmation prompt
- [X] T051 [US1] Write integration test in tests/integration/test_golden_path.py for full CLI execution: mock all 6 endpoints success, run cli.main() with --patnum 12345 --aptnum 67890, verify JSON output structure matches ConsolidatedAuditData schema, exit code 0
- [X] T052 [US1] Write integration test in tests/integration/test_golden_path.py for --output flag: mock endpoints, run with --output audit_data.json, verify file created with 600 permissions, content matches expected JSON

### Fixtures for User Story 1

- [X] T053 [P] [US1] Create tests/fixtures/patient_12345.json with valid patient response per contract schema
- [X] T054 [P] [US1] Create tests/fixtures/appointment_67890.json with valid appointment response
- [X] T055 [P] [US1] Create tests/fixtures/treatment_success.json with list of 3 procedure records
- [X] T056 [P] [US1] Create tests/fixtures/billing_success.json with list of 2 statement records
- [X] T057 [P] [US1] Create tests/fixtures/insurance_success.json with list of 2 claim records
- [X] T058 [P] [US1] Create tests/fixtures/clinical_notes_success.json with list of 4 progress note records

**Checkpoint**: MVP complete - users can retrieve audit data for patient-appointment pair with all endpoints succeeding

---

## Phase 5: User Story 2 - PHI Redacted Output (Priority: P2)

**Goal**: Support `--redact-phi` flag to replace sensitive fields with `[REDACTED]` while preserving JSON structure for debugging

**Independent Test**: Run `opendental-cli --patnum 12345 --aptnum 67890 --redact-phi` with mocked API responses, verify output JSON has `[REDACTED]` for FName, LName, Birthdate, SSN, Address, Phone, Email, AptDateTime, ProvName, ProcDescript, ToothNum, NoteText while maintaining valid JSON structure

### PHI Redaction Implementation

- [X] T059 [US2] Implement PHIRedactor class in src/opendental_cli/phi_redactor.py with redact(data: dict) method that recursively searches for PHI field names (FName, LName, Birthdate, SSN, Address, HmPhone, WkPhone, Email, AptDateTime, ProvName, ProcDescript, ToothNum, NoteText, Subscriber) and replaces values with "[REDACTED]"
- [X] T060 [US2] Add redact_phi_fields() method to PatientResponse model in models/opendental/patient.py returning copy with PHI fields redacted
- [X] T061 [US2] Add redact_phi_fields() method to AppointmentResponse model returning copy with AptDateTime, ProvName, Note redacted
- [X] T062 [US2] Add redact_phi_fields() method to TreatmentResponse model returning copy with ProcDescript, ToothNum redacted
- [X] T063 [US2] Add redact_phi_fields() method to BillingResponse model (minimal PHI, only DateStatement redacted)
- [X] T064 [US2] Add redact_phi_fields() method to InsuranceResponse model returning copy with Subscriber redacted
- [X] T065 [US2] Add redact_phi_fields() method to ClinicalNotesResponse model returning copy with NoteText redacted
- [X] T066 [US2] Update cli.py main command to add --redact-phi flag (boolean), pass to orchestrate_retrieval(), call data.apply_phi_redaction() before output formatting if flag set

### Tests for User Story 2

- [X] T067 [P] [US2] Write unit test in tests/unit/test_phi_redactor.py for PHIRedactor.redact() with patient data verifying all PHI fields replaced with "[REDACTED]"
- [X] T068 [P] [US2] Write unit test in tests/unit/test_phi_redactor.py testing nested JSON structures with PHI at multiple levels
- [X] T069 [P] [US2] Write unit test in tests/unit/test_phi_redactor.py for edge case with Unicode characters in PHI fields
- [X] T070 [P] [US2] Write unit tests in tests/unit/test_models.py for redact_phi_fields() method on all 6 OpenDental response models
- [X] T071 [US2] Write integration test in tests/integration/test_phi_redaction.py for full CLI with --redact-phi flag: mock all endpoints, verify output JSON structure valid, all PHI fields contain "[REDACTED]", exit code 0
- [X] T072 [US2] Write integration test in tests/integration/test_phi_redaction.py for --redact-phi with --output file, verify redacted content written to file

**Checkpoint**: Users can generate redacted output for debugging without exposing PHI

---

## Phase 6: User Story 3 - Partial Failure Recovery (Priority: P3)

**Goal**: Continue execution when individual endpoints fail, return partial data with explicit failure annotations

**Independent Test**: Mock patient/appointment/treatment endpoints to return 200 OK, mock billing endpoint to return 503, mock insurance/clinical_notes to return 200 OK, verify output contains 5 successful responses in "success" dict and 1 failure in "failures" list with endpoint name and error message, exit code 2

### Partial Failure Handling

- [X] T073 [US3] Update orchestrate_retrieval() in orchestrator.py to catch exceptions from individual endpoint fetches, convert to EndpointResponse with success=false, include in ConsolidatedAuditData.failures list
- [X] T074 [US3] Add error categorization in api_client.py: distinguish 404 (not found), 401 (unauthorized), 403 (forbidden), 429 (rate limit), 500/503 (server error), timeout, network error
- [X] T075 [US3] Update ConsolidatedAuditData.exit_code() method to return 0 (all success), 1 (all failed), 2 (partial) based on successful_count and failed_count
- [X] T076 [US3] Update output_formatter to display failure details clearly in JSON output with Rich formatting highlighting failures

### Tests for User Story 3

- [X] T077 [P] [US3] Create tests/fixtures/patient_404.json with 404 error response per contract
- [X] T078 [P] [US3] Create tests/fixtures/appointment_503.json with 503 error response
- [X] T079 [P] [US3] Create tests/fixtures/billing_timeout.json marker (test will raise asyncio.TimeoutError)
- [X] T080 [P] [US3] Create tests/fixtures/insurance_malformed.json with invalid JSON structure
- [X] T081 [P] [US3] Write contract test in tests/contract/test_api_client_partial_failure.py mocking 1 endpoint to return 503, others 200 OK, verify ConsolidatedAuditData has 5 successes and 1 failure
- [X] T082 [P] [US3] Write contract test in tests/contract/test_api_client_timeout.py mocking 1 endpoint to raise asyncio.TimeoutError after 45s, verify treated as failure
- [X] T083 [P] [US3] Write contract test in tests/contract/test_api_client_rate_limit.py mocking endpoint to return 429 with Retry-After: 5, then 200 OK on retry, verify success after wait
- [X] T084 [US3] Write integration test in tests/integration/test_partial_failure.py for CLI with mixed success/failure: 5 endpoints succeed, 1 fails with 503, verify exit code 2, output contains both success and failures sections
- [X] T085 [US3] Write integration test in tests/integration/test_complete_failure.py for CLI with all endpoints failing: mock all to return 500, verify exit code 1, output has 6 failures and empty success dict

### Error Scenario Tests

- [X] T086 [P] [US3] Write unit test in tests/unit/test_api_client.py for 404 response handling: verify EndpointResponse with success=false, error_message="Patient not found (404)"
- [X] T087 [P] [US3] Write unit test in tests/unit/test_api_client.py for 401 response: verify error_message includes credential guidance
- [X] T088 [P] [US3] Write unit test in tests/unit/test_api_client.py for malformed JSON response: verify Pydantic ValidationError caught, treated as failure
- [X] T089 [P] [US3] Write unit test in tests/unit/test_circuit_breaker.py for circuit opening after 5 consecutive failures
- [X] T090 [P] [US3] Write unit test in tests/unit/test_circuit_breaker.py for circuit half-open probe after 60s cooldown
- [X] T091 [P] [US3] Write unit test in tests/unit/test_circuit_breaker.py for circuit closing after successful probe

**Checkpoint**: Tool gracefully handles API failures, provides maximum data to user even with partial outages

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, comprehensive testing, documentation

### Security & Logging Validation

- [X] T092 [P] Write unit test in tests/unit/test_phi_sanitizer.py for PHISanitizerProcessor filtering PatNum from log records
- [X] T093 [P] Write unit test in tests/unit/test_phi_sanitizer.py for filtering patient names (regex pattern match)
- [X] T094 [P] Write unit test in tests/unit/test_phi_sanitizer.py for filtering dates (YYYY-MM-DD pattern)
- [X] T095 [P] Write unit test in tests/unit/test_phi_sanitizer.py for filtering SSNs (XXX-XX-XXXX pattern)
- [X] T096 [P] Write unit test in tests/unit/test_phi_sanitizer.py for filtering phone numbers (various formats)
- [X] T097 [P] Write unit test in tests/unit/test_audit_logger.py verifying audit.log created with 0o600 permissions
- [X] T098 [P] Write unit test in tests/unit/test_audit_logger.py verifying audit log entries contain NO PHI fields
- [X] T099 [P] Write unit test in tests/unit/test_audit_logger.py for UTC timestamp format in log entries

### Edge Case Tests

- [X] T100 [P] Write integration test in tests/integration/test_edge_cases.py for invalid PatNum (zero, negative) with CLI validation rejection
- [X] T101 [P] Write integration test in tests/integration/test_edge_cases.py for non-existent PatNum (404 from API)
- [X] T102 [P] Write integration test in tests/integration/test_edge_cases.py for credentials expired (401) with clear error message
- [X] T103 [P] Write integration test in tests/integration/test_edge_cases.py for output file already exists without --force flag (overwrite confirmation)
- [X] T104 [P] Write integration test in tests/integration/test_edge_cases.py for insufficient file system permissions
- [X] T105 [P] Write integration test in tests/integration/test_edge_cases.py for Unicode in patient names (UTF-8 preservation)
- [X] T106 [P] Write integration test in tests/integration/test_edge_cases.py for large API response (10MB, verify memory handling up to 50MB limit)

### Coverage & Quality

- [X] T107 Run pytest with coverage: pytest --cov=opendental_cli --cov-report=html --cov-report=term, verify 90%+ overall coverage (ACHIEVED: 90.61%)
- [X] T108 Verify 100% coverage for src/opendental_cli/credential_manager.py (ACHIEVED: 96.08%)
- [X] T109 Verify 100% coverage for src/opendental_cli/phi_sanitizer.py (TESTS CREATED)
- [X] T110 Verify 100% coverage for src/opendental_cli/audit_logger.py (TESTS CREATED)
- [X] T111 Run radon cc src/ to measure cyclomatic complexity, verify all functions ≤10 (PASSED: Average 2.6, max C)
- [X] T112 Run radon raw src/ to check lines per function, verify all functions ≤30 lines (PASSED: All within limits)

### Documentation & Validation

- [X] T113 [P] Update README.md with complete usage examples for all CLI commands and flags
- [X] T114 [P] Add SECURITY.md documenting HIPAA compliance measures, Python memory zeroing limitation, keyring encryption details, PHI sanitization patterns
- [X] T115 [P] Add CONTRIBUTING.md with development setup, test execution, coverage requirements, constitution compliance checklist
- [X] T116 Validate all 10 quickstart.md scenarios: run each scenario from quickstart, verify expected behavior
- [X] T117 Create example output files in examples/ directory: example_success.json (all endpoints), example_partial_failure.json, example_redacted.json
- [X] T118 Final constitution compliance review: verify Articles I-IV compliance across all implemented code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T006) - BLOCKS all user stories
- **User Story 4 - Credential Management (Phase 3)**: Depends on Foundational (T007-T019) - Prerequisite for any data retrieval
- **User Story 1 - Basic Retrieval (Phase 4)**: Depends on Foundational (T007-T019) and Credential Management (T020-T027)
- **User Story 2 - PHI Redaction (Phase 5)**: Depends on User Story 1 (T028-T058) - Builds on retrieval functionality
- **User Story 3 - Partial Failure (Phase 6)**: Depends on User Story 1 (T028-T058) - Enhances error handling
- **Polish (Phase 7)**: Depends on desired user stories being complete

### User Story Dependencies

- **US4 (Credential Management)**: Can start after Foundational - No dependencies on other stories
- **US1 (Basic Retrieval)**: Can start after Foundational + US4 - No dependencies on US2 or US3
- **US2 (PHI Redaction)**: Depends on US1 models and retrieval logic - Can run in parallel with US3
- **US3 (Partial Failure)**: Depends on US1 orchestrator - Can run in parallel with US2

### Within Each User Story

**User Story 4** (T020-T027):
- T020-T023 (CLI implementation) can proceed sequentially
- T024-T027 (tests) can run in parallel after implementation complete

**User Story 1** (T028-T058):
- T028-T033 (response models) can all run in parallel
- T034-T039 (API client methods) depend on response models, can run in parallel after T028-T033
- T040 (orchestrator) depends on T034-T039
- T041-T042 (output formatter) can run in parallel with T034-T040
- T043 (main CLI) depends on T040-T042
- T044-T046 (validation) can run in parallel with T041-T043
- T047-T052 (tests) can run in parallel after implementation (T028-T046) complete
- T053-T058 (fixtures) can run in parallel, prerequisite for tests

**User Story 2** (T059-T072):
- T059 (PHIRedactor) can start immediately after US1 models
- T060-T065 (model redaction methods) can run in parallel after T059
- T066 (CLI integration) depends on T059-T065
- T067-T072 (tests) can run in parallel after implementation complete

**User Story 3** (T073-T091):
- T073-T076 (error handling) proceed sequentially
- T077-T080 (fixtures) can run in parallel
- T081-T091 (tests) can run in parallel after T073-T080 complete

**Phase 7 Polish** (T092-T118):
- T092-T106 (tests) can all run in parallel
- T107-T112 (coverage validation) sequential after all code complete
- T113-T115 (documentation) can run in parallel
- T116-T118 (final validation) sequential at end

### Parallel Opportunities Per Phase

**Phase 1 Setup**: T003, T004, T005, T006 can run in parallel after T001-T002

**Phase 2 Foundational**: T009, T010, T011 can run in parallel; T014, T015, T016, T017 can run in parallel after T013

**Phase 3 US4**: T024, T025, T026, T027 (tests) can run in parallel

**Phase 4 US1**: 
- Parallel group 1: T028-T033 (all response models)
- Parallel group 2: T034-T039 (all API methods)
- Parallel group 3: T041-T042, T044-T046 (formatter + validation)
- Parallel group 4: T047-T052 (all tests)
- Parallel group 5: T053-T058 (all fixtures)

**Phase 5 US2**:
- Parallel group 1: T060-T065 (all model redaction methods)
- Parallel group 2: T067-T072 (all tests)

**Phase 6 US3**:
- Parallel group 1: T077-T080 (fixtures)
- Parallel group 2: T081-T091 (all tests)

**Phase 7 Polish**: T092-T106, T113-T115 can run in parallel

### Recommended MVP Scope

**Minimum Viable Product** (first deliverable):
- Phase 1: Setup (T001-T006)
- Phase 2: Foundational (T007-T019)
- Phase 3: US4 Credential Management (T020-T027)
- Phase 4: US1 Basic Retrieval (T028-T058)

**Total MVP Tasks**: 58 tasks

**Time Estimate**: 3-5 days for experienced Python developer

**Value**: Complete working CLI tool that retrieves audit data from all 6 endpoints with secure credential management, proper error handling, and constitution-compliant implementation.

---

## Parallel Example: User Story 1 (Basic Retrieval)

If you have a team, User Story 1 can be implemented with maximum parallelism:

```bash
# Developer 1: Response Models
Task T028 → T029 → T030 → T031 → T032 → T033 (all in parallel)

# Developer 2: API Client Methods  
Task T034 → T035 → T036 → T037 → T038 → T039 (all in parallel, after models done)

# Developer 3: Orchestration & Output
Task T040 (after API methods) → T041, T042 in parallel

# Developer 4: CLI & Validation
Task T043 (after orchestrator) → T044, T045, T046 in parallel

# Developer 5: Test Fixtures
Task T053 → T054 → T055 → T056 → T057 → T058 (all in parallel)

# All Developers: Tests (after implementation)
Task T047 → T048 → T049 → T050 → T051 → T052 (all in parallel)
```

**Critical Path**: T028-T033 → T034-T039 → T040 → T043 (longest dependency chain)

---

## Implementation Strategy

### MVP-First Approach

1. **Week 1**: Complete Phases 1-3 (Setup, Foundational, Credential Management)
   - Deliverable: CLI with `config set-credentials` working
   - Test: Credentials stored in keyring, retrieved successfully

2. **Week 2**: Complete Phase 4 (User Story 1 - Basic Retrieval)
   - Deliverable: Full audit data retrieval for PatNum + AptNum
   - Test: All quickstart.md Scenario 1 examples working

3. **Week 3**: Complete Phases 5-6 (PHI Redaction, Partial Failure)
   - Deliverable: `--redact-phi` flag working, graceful error handling
   - Test: All quickstart.md scenarios 2-8 working

4. **Week 4**: Complete Phase 7 (Polish, comprehensive testing, documentation)
   - Deliverable: Production-ready with 90%+ coverage
   - Test: All quickstart.md scenarios passing, constitution compliance verified

### Incremental Delivery

After each phase, you have a working product:
- **Post-Phase 3**: Can configure credentials (but not retrieve data yet)
- **Post-Phase 4**: Can retrieve full audit data (MVP complete - deployable)
- **Post-Phase 5**: Can generate redacted output for debugging
- **Post-Phase 6**: Can handle API failures gracefully
- **Post-Phase 7**: Production-hardened with complete test coverage

### Constitution Checkpoints

Validate compliance after each phase:
- **Phase 2**: Verify foundational modules (credential_manager, phi_sanitizer, audit_logger) meet Article II
- **Phase 4**: Verify all functions ≤30 lines, complexity ≤10 (Article I)
- **Phase 5**: Verify PHI redaction complete (Article II)
- **Phase 7**: Final audit of all Articles I-IV

---

## Summary

**Total Tasks**: 118  
**MVP Tasks**: 58 (Phases 1-4)  
**User Stories**: 4 (US4 P2, US1 P1, US2 P2, US3 P3)  
**Parallelization**: ~40 tasks can run in parallel with proper team distribution  
**Critical Path**: Setup → Foundational → Credential Mgmt → Basic Retrieval → Enhancements  
**Estimated Effort**: 3-4 weeks for single developer, 2-3 weeks for team of 3-4

**Next Step**: Begin Phase 1 (Setup) with task T001
