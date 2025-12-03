# Tasks: OpenDental API Endpoint Authorization & Format Fix

**Input**: Design documents from `/specs/002-endpoint-auth-fix/`
**Prerequisites**: plan.md, spec.md

**Tests**: Tests are included to validate fixes against actual API contract specifications

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `- [ ] [ID] [P?] [Story] Description`

- **Checkbox**: ALWAYS starts with `- [ ]` (markdown checkbox)
- **[ID]**: Task ID (T001, T002, T003...)
- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (e.g., [US1], [US2], [US3]) - only for user story phases
- **Description**: Clear action with exact file path

---

## Phase 1: Research & Discovery

**Purpose**: Understand current implementation issues and identify root causes

- [X] T001 Audit current authentication implementation in src/opendental_cli/models/credential.py and src/opendental_cli/api_client.py to identify how headers are constructed vs contract specification
- [X] T002 [P] Audit endpoint URL construction in all 6 fetch_* methods in src/opendental_cli/api_client.py to compare HTTP methods, path formats, and parameter names against specs/001-audit-data-cli/contracts/opendental-api.md
- [X] T003 [P] Create specs/002-endpoint-auth-fix/research.md documenting authentication audit, endpoint format audit, and live API test results (if credentials available)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix authentication infrastructure that ALL endpoints depend on

**⚠️ CRITICAL**: No endpoint fixes can work until authentication is correct

- [X] T004 Update APICredential model in src/opendental_cli/models/credential.py to use developer_key and customer_key fields (replacing single api_key field) - **ALREADY IMPLEMENTED**
- [X] T005 Update get_auth_header() method in src/opendental_cli/models/credential.py to return dict with "DeveloperKey" and "CustomerKey" headers - **ALREADY IMPLEMENTED**
- [X] T006 Update set_credentials() in src/opendental_cli/credential_manager.py to accept developer_key and customer_key parameters, store both in keyring as {environment}_developer_key and {environment}_customer_key - **ALREADY IMPLEMENTED**
- [X] T007 Update _get_from_keyring() in src/opendental_cli/credential_manager.py to retrieve both developer_key and customer_key from keyring - **ALREADY IMPLEMENTED**
- [X] T008 Update _get_from_env() in src/opendental_cli/credential_manager.py to check OPENDENTAL_DEVELOPER_KEY and OPENDENTAL_CUSTOMER_KEY environment variables - **ALREADY IMPLEMENTED**
- [X] T009 Update config set-credentials command in src/opendental_cli/cli.py to prompt separately for "Developer Key" and "Customer Key" and pass both to credential_manager.set_credentials() - **ALREADY IMPLEMENTED**

**Checkpoint**: Authentication foundation ready - endpoint fixes can now proceed - **✅ PASSED (Already Correct)**

---

## Phase 3: User Story 1 - Diagnose API Communication Failures (Priority: P1)

**Goal**: Identify and document specific mismatches between implementation and API contract

**Independent Test**: Review research.md and verify all discrepancies are documented with evidence from code comparison and API testing

### Implementation for User Story 1

- [ ] T010 [US1] Compare authentication header construction in src/opendental_cli/models/credential.py against specs/001-audit-data-cli/contracts/opendental-api.md authentication section, document discrepancies in research.md
- [ ] T011 [P] [US1] Create comparison table in research.md showing implemented vs contract-specified format for all 6 endpoints (method, path, params)
- [ ] T012 [P] [US1] If test credentials available, run opendental-cli --patnum 12345 --aptnum 67890 and capture error codes/messages in research.md to distinguish auth failures (401/403) from format errors (400/404)

**Checkpoint**: Root causes identified - ready to implement fixes

---

## Phase 4: User Story 2 - Fix Authentication Header Format (Priority: P1) 🎯 MVP BLOCKER

**Goal**: Ensure API requests send DeveloperKey and CustomerKey headers in correct format

**Independent Test**: Configure valid credentials, make test request to /allergies endpoint, verify 200 response instead of 401/403

### Tests for User Story 2

- [ ] T013 [P] [US2] Update unit test in tests/unit/test_models.py to verify APICredential model accepts both developer_key and customer_key fields
- [ ] T014 [P] [US2] Update unit test in tests/unit/test_models.py to verify get_auth_header() returns dict with "DeveloperKey" and "CustomerKey" keys
- [ ] T015 [P] [US2] Update unit tests in tests/unit/test_credential_manager.py to verify set_credentials() stores both keys in keyring
- [ ] T016 [P] [US2] Update unit tests in tests/unit/test_credential_manager.py to verify _get_from_keyring() retrieves both keys
- [ ] T017 [P] [US2] Update unit tests in tests/unit/test_credential_manager.py to verify _get_from_env() checks both OPENDENTAL_DEVELOPER_KEY and OPENDENTAL_CUSTOMER_KEY
- [ ] T018 [P] [US2] Update integration tests in tests/integration/test_credential_flow.py to test config set-credentials with both key prompts

### Implementation for User Story 2

Note: Implementation already completed in Phase 2 Foundational tasks (T004-T009)

- [ ] T019 [US2] Verify OpenDentalAPIClient.__init__() in src/opendental_cli/api_client.py correctly spreads credential.get_auth_header() into HTTPX client headers
- [ ] T020 [US2] Add debug logging in src/opendental_cli/api_client.py to confirm DeveloperKey and CustomerKey headers are set on requests (non-PHI logging)

**Checkpoint**: Authentication headers correct - all endpoints should now authenticate successfully

---

## Phase 5: User Story 3 - Fix Endpoint Request Formats (Priority: P2)

**Goal**: Ensure each endpoint uses correct HTTP method, URL path format, and parameter names

**Independent Test**: With working authentication, test all 6 endpoints individually, verify 200 responses with valid data structure

### Tests for User Story 3

- [ ] T021 [P] [US3] Update contract test in tests/contract/test_api_client_golden_path.py to verify fetch_patient_notes(12345) calls GET /patientnotes/12345 (path param, not query)
- [ ] T022 [P] [US3] Update contract test in tests/contract/test_api_client_golden_path.py to verify fetch_vital_signs(67890) uses PUT method with JSON body containing "Query" key (capital Q)
- [ ] T023 [P] [US3] Update contract tests for all 6 endpoints to verify query parameter casing matches contract (AptNum, PatNum with capital letters)
- [ ] T024 [P] [US3] Update all test fixtures in tests/fixtures/ to match actual API response structure per contract specifications

### Implementation for User Story 3

- [X] T025 [P] [US3] Fix fetch_patient_notes() in src/opendental_cli/api_client.py to use path parameter format: /patientnotes/{patnum} instead of query parameter - **ALREADY CORRECT**
- [X] T026 [P] [US3] Verify fetch_vital_signs() in src/opendental_cli/api_client.py uses "query" key (lowercase q) in JSON body and correct SQL column names - **FIXED: Changed "Query" to "query"**
- [X] T027 [P] [US3] Verify query parameter casing in fetch_procedure_logs(), fetch_allergies(), fetch_medications(), and fetch_problems() matches contract (AptNum, PatNum with capitals) - **ALREADY CORRECT**
- [ ] T028 [US3] Run integration test in tests/integration/test_golden_path.py to verify all 6 endpoints return 200 OK with valid data

**Checkpoint**: All endpoints correctly formatted - full audit retrieval should now work end-to-end - **⚠️ READY FOR TESTING**

---

## Phase 6: User Story 4 - Update Tests and Documentation (Priority: P3)

**Goal**: Ensure documentation and tests reflect corrected implementation

**Independent Test**: All tests pass, documentation accurately describes two-key authentication and correct endpoint formats

### Documentation for User Story 4

- [ ] T029 [P] [US4] Update specs/001-audit-data-cli/contracts/opendental-api.md with verified endpoint specifications including curl examples with DeveloperKey and CustomerKey headers
- [ ] T030 [P] [US4] Update README.md "Configure Credentials" section to document both Developer Key and Customer Key, update environment variable examples (OPENDENTAL_DEVELOPER_KEY, OPENDENTAL_CUSTOMER_KEY)
- [ ] T031 [P] [US4] Add troubleshooting section to README.md for common authentication errors (401/403) and endpoint format errors (400/404)

### Tests for User Story 4

- [ ] T032 [P] [US4] Update all respx mocks in tests/contract/ to match corrected URLs (e.g., /patientnotes/{patnum} format)
- [ ] T033 [P] [US4] Update integration tests in tests/integration/test_edge_cases.py to verify error handling for 401 (invalid credentials) and 403 (insufficient permissions)
- [ ] T034 [US4] Run full test suite: pytest tests/ -v --cov=opendental_cli --cov-report=term to verify 90%+ coverage maintained

**Checkpoint**: Documentation and tests updated - feature complete

---

## Phase 7: Validation & Deployment

**Purpose**: End-to-end validation and deployment readiness

- [ ] T035 Manual end-to-end test: Reset credentials, set new password, configure both keys via config set-credentials, run full audit retrieval with opendental-cli --patnum 12345 --aptnum 67890, verify exit code 0 and all 6 endpoints in success section
- [ ] T036 [P] Run full test suite with pytest tests/unit/ tests/contract/ tests/integration/ -v and verify 0 failures
- [ ] T037 [P] Verify all 6 endpoints return 200 OK: procedure_logs, allergies, medications, problems, patient_notes, vital_signs
- [ ] T038 [P] Update SECURITY.md if credential storage format changed (document two-key storage approach)
- [ ] T039 Document manual test results in specs/002-endpoint-auth-fix/research.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Research (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Can start after Research - BLOCKS all user stories
- **User Story 1 - Diagnose (Phase 3)**: Can run in parallel with Research (Phase 1)
- **User Story 2 - Fix Auth (Phase 4)**: Depends on Foundational (Phase 2) completion
- **User Story 3 - Fix Endpoints (Phase 5)**: Depends on User Story 2 (authentication must work first)
- **User Story 4 - Documentation (Phase 6)**: Depends on User Stories 2 & 3 completion
- **Validation (Phase 7)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Diagnose)**: Can start immediately - No dependencies
- **US2 (Fix Auth)**: Depends on Foundational (T004-T009) - BLOCKS US3
- **US3 (Fix Endpoints)**: Depends on US2 - Endpoints won't work without correct auth
- **US4 (Documentation)**: Depends on US2 & US3 - Must document working implementation

### Within Each User Story

**User Story 2** (T013-T020):
- T013-T018 (tests) can all run in parallel after Foundational phase
- T019-T020 (verification) depend on Foundational implementation

**User Story 3** (T021-T028):
- T021-T024 (tests) can all run in parallel
- T025-T027 (endpoint fixes) can run in parallel
- T028 (integration test) depends on T025-T027 completion

**User Story 4** (T029-T034):
- T029-T031 (documentation) can all run in parallel
- T032-T033 (tests) can run in parallel
- T034 (full suite) depends on all other US4 tasks

### Parallel Opportunities Per Phase

**Phase 1 Research**: T002 and T003 can run in parallel with T001

**Phase 2 Foundational**: T004-T005 must be sequential (model first, then header method), T006-T008 can run in parallel after T004-T005, T009 depends on T006

**Phase 3 US1**: T010-T012 can all run in parallel

**Phase 4 US2**: T013-T018 (all tests) can run in parallel, T019-T020 (verification) can run in parallel

**Phase 5 US3**: 
- Parallel group 1: T021-T024 (all tests)
- Parallel group 2: T025-T027 (endpoint fixes)

**Phase 6 US4**:
- Parallel group 1: T029-T031 (documentation)
- Parallel group 2: T032-T033 (tests)

**Phase 7 Validation**: T036-T038 can run in parallel after T035

### Critical Path

T001 → T004 → T005 → T006 → T009 → T019 → T020 → T025 → T028 → T035

**Estimated Time**: 4.5 hours total
- Research: 1.5 hours
- Foundational + US2: 1 hour
- US3: 35 minutes
- US4 + Validation: 1.5 hours

---

## Implementation Strategy

### MVP First Approach

1. **Phase 1-2**: Research + Fix Authentication (2.5 hours)
   - Deliverable: Authentication works, get 200 from at least one endpoint
   - Test: `opendental-cli config set-credentials` accepts both keys

2. **Phase 5**: Fix Endpoint Formats (35 minutes)
   - Deliverable: All 6 endpoints return 200 OK
   - Test: Full audit retrieval succeeds

3. **Phase 6-7**: Documentation + Validation (1.5 hours)
   - Deliverable: Tests pass, documentation updated
   - Test: All test suites green

### Incremental Delivery

After each phase, you have progressively working functionality:
- **Post-Phase 2**: Can configure credentials with both keys (but endpoints may still fail)
- **Post-Phase 4**: Authentication works (endpoints return 200 instead of 401/403)
- **Post-Phase 5**: All endpoints work correctly (full audit retrieval succeeds)
- **Post-Phase 6**: Production-ready with complete documentation and tests

---

## Summary

**Total Tasks**: 39
**MVP Tasks**: 20 (Phases 1-5 core implementation)
**User Stories**: 4 (US1 P1 Diagnose, US2 P1 Fix Auth, US3 P2 Fix Endpoints, US4 P3 Documentation)
**Parallelization**: ~18 tasks can run in parallel with proper sequencing
**Critical Path**: Research → Foundational Auth → Endpoint Fixes → Validation
**Estimated Effort**: 4.5 hours for single developer

**Key Risks**:
- Existing stored credentials may need migration to two-key format
- Breaking change to credential storage
- Requires valid test credentials for live API testing

**Success Metrics**:
- All 6 endpoints return 200 OK
- 0 authentication errors (401/403)
- 0 format errors (400/404)
- 100% of tests passing

**Next Step**: Begin Phase 1 (Research) with task T001
