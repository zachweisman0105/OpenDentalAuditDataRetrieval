# Tasks: Fix OpenDental FHIR Authorization Format

**Input**: Design documents from `/specs/main/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Tests are included to validate the authorization format fix

**Organization**: Tasks are grouped by user story to enable focused implementation and independent testing

---

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **Checkbox**: ALWAYS starts with `- [ ]` (markdown checkbox)
- **[ID]**: Task ID (T001, T002, T003...)
- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (e.g., [US1], [US2], [US3]) - only for user story phases
- **Description**: Clear action with exact file path

---

## Phase 1: Setup & Validation

**Purpose**: Validate current state and prepare for fix

- [X] T001 Verify current implementation in src/opendental_cli/models/credential.py returns separate DeveloperKey and CustomerKey headers
- [X] T002 [P] Confirm api_client.py correctly spreads headers using **credential.get_auth_header()
- [X] T003 [P] Document current test expectations for authentication headers in tests/unit/test_models.py

**Checkpoint**: Current state documented - ready to implement fix

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix core authorization header format that ALL endpoints depend on

**⚠️ CRITICAL**: This change fixes 401 errors on all API endpoints

### US1: Fix Authorization Header Format (Priority: P0) 🎯 MVP BLOCKER

**Goal**: Update credential model to generate correct ODFHIR authorization header

**Independent Test**: Unit test verifies header format is `Authorization: ODFHIR {key1}/{key2}`

#### Implementation for US1

- [X] T004 [US1] Update get_auth_header() in src/opendental_cli/models/credential.py to return single Authorization header with ODFHIR format
- [X] T005 [US1] Add comprehensive docstring to get_auth_header() explaining ODFHIR authentication scheme and format requirements

**Checkpoint**: Authorization header format corrected - ready for test validation

---

## Phase 3: Test Validation

**Purpose**: Verify authorization format with comprehensive test coverage

### US1: Unit Tests

- [X] T006 [P] [US1] Add test_credential_get_auth_header_odfhir_format in tests/unit/test_models.py to verify Authorization header format
- [X] T007 [P] [US1] Add test_credential_get_auth_header_uses_secret_values in tests/unit/test_models.py to verify SecretStr extraction
- [X] T008 [P] [US1] Add test_credential_get_auth_header_no_custom_headers in tests/unit/test_models.py to verify old DeveloperKey/CustomerKey headers removed

### US1: Contract Tests

- [X] T009 [P] [US1] Update test_fetch_procedure_logs_golden_path in tests/contract/test_api_client_golden_path.py to verify Authorization header sent
- [X] T010 [P] [US1] Update test_fetch_allergies_golden_path in tests/contract/test_api_client_golden_path.py to verify Authorization header sent
- [X] T011 [P] [US1] Update test_fetch_medications_golden_path in tests/contract/test_api_client_golden_path.py to verify Authorization header sent
- [X] T012 [P] [US1] Update test_fetch_problems_golden_path in tests/contract/test_api_client_golden_path.py to verify Authorization header sent
- [X] T013 [P] [US1] Update test_fetch_patient_notes_golden_path in tests/contract/test_api_client_golden_path.py to verify Authorization header sent
- [X] T014 [P] [US1] Update test_fetch_vital_signs_golden_path in tests/contract/test_api_client_golden_path.py to verify Authorization header sent
- [X] T015 [US1] Update test_all_endpoints_golden_path in tests/contract/test_api_client_golden_path.py to verify Authorization header on all requests

### US1: Contract Tests - Error Scenarios

- [X] T016 [P] [US1] Update test_partial_failure_with_503_response in tests/contract/test_api_client_partial_failure.py to verify Authorization header
- [X] T017 [P] [US1] Update test_rate_limit_429_with_retry_success in tests/contract/test_api_client_rate_limit.py to verify Authorization header
- [X] T018 [P] [US1] Update test_timeout_after_45_seconds in tests/contract/test_api_client_timeout.py to verify Authorization header

### US1: Additional Unit Tests

- [X] T019 [P] [US1] Update any existing unit tests in tests/unit/test_api_client.py that verify authentication headers
- [X] T020 [P] [US1] Update test_404_response_handling in tests/unit/test_api_client.py if it checks headers
- [X] T021 [P] [US1] Update test_401_response_with_credential_guidance in tests/unit/test_api_client.py if it checks headers

**Checkpoint**: All tests updated and passing - authorization format validated

---

## Phase 4: US2 - Improve User Experience (Priority: P1)

**Goal**: Update CLI prompts and documentation for clarity

**Independent Test**: Run `opendental-cli config set-credentials` and verify clear prompts

### Implementation for US2

- [X] T022 [US2] Update credential prompt in src/opendental_cli/cli.py to change "Customer Key" to "Developer Portal Key"
- [X] T023 [P] [US2] Update API contract documentation in specs/001-audit-data-cli/contracts/opendental-api.md to document ODFHIR format
- [X] T024 [P] [US2] Add ODFHIR authentication examples to all 6 endpoint documentation sections in specs/001-audit-data-cli/contracts/opendental-api.md

**Checkpoint**: CLI prompts clear, documentation accurate

---

## Phase 5: US3 - Integration Test Validation (Priority: P1)

**Goal**: Verify full CLI workflow with ODFHIR authorization

**Independent Test**: Integration tests pass with mocked Authorization header

### Tests for US3

- [X] T025 [P] [US3] Update test_golden_path_stdout in tests/integration/test_golden_path.py to verify Authorization header accepted
- [X] T026 [P] [US3] Update test_golden_path_file_output in tests/integration/test_golden_path.py to verify Authorization header accepted
- [X] T027 [P] [US3] Update test_partial_failure_one_endpoint in tests/integration/test_partial_failure.py to verify Authorization header
- [X] T028 [P] [US3] Update test_complete_failure_all_endpoints in tests/integration/test_partial_failure.py to verify Authorization header
- [X] T029 [P] [US3] Update test_partial_failure_with_output_file in tests/integration/test_partial_failure.py to verify Authorization header
- [X] T030 [P] [US3] Update test_redact_phi_stdout in tests/integration/test_phi_redaction.py to verify Authorization header
- [X] T031 [P] [US3] Update test_redact_phi_file_output in tests/integration/test_phi_redaction.py to verify Authorization header

### Edge Case Tests for US3

- [X] T032 [P] [US3] Update test_non_existent_patnum_404 in tests/integration/test_edge_cases.py to verify Authorization header
- [X] T033 [P] [US3] Update test_credentials_expired_401 in tests/integration/test_edge_cases.py to verify Authorization header with auth failure
- [X] T034 [P] [US3] Update test_output_file_overwrite_confirmation in tests/integration/test_edge_cases.py if it makes API calls
- [X] T035 [P] [US3] Update test_unicode_patient_names in tests/integration/test_edge_cases.py to verify Authorization header

**Checkpoint**: Full integration tests passing with ODFHIR format

---

## Phase 6: Polish & Documentation

**Purpose**: Complete documentation and final validation

- [ ] T036 [P] Add "Authentication" section to README.md explaining ODFHIR format and credential configuration
- [ ] T037 [P] Update SECURITY.md to document ODFHIR authorization format and security guarantees
- [ ] T038 Run full test suite with pytest --cov to verify ≥90% coverage maintained
- [ ] T039 Verify no PHI is logged in error messages or debug output during test runs
- [ ] T040 Run quickstart.md validation steps to ensure all documentation is accurate

**Checkpoint**: Documentation complete, all tests passing

---

## Phase 7: Manual Verification

**Purpose**: Validate fix with real API credentials

**⚠️ REQUIRES**: Valid OpenDental credentials

- [ ] T041 Run opendental-cli config set-credentials to configure credentials (if not already done)
- [ ] T042 Execute opendental-cli --patnum 12345 --aptnum 67890 with real credentials
- [ ] T043 Verify all 6 endpoints return 200 OK instead of 401 Unauthorized
- [ ] T044 Verify JSON output contains expected patient/appointment data
- [ ] T045 Check that no PHI is logged to console or log files

**Checkpoint**: Real API calls successful - fix validated end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

1. **Phase 1 (Setup)**: No dependencies - can start immediately
2. **Phase 2 (Foundational - US1 Implementation)**: Depends on Phase 1 - BLOCKS all other phases
3. **Phase 3 (US1 Tests)**: Depends on Phase 2 (T004-T005 complete)
4. **Phase 4 (US2 Documentation)**: Can run in parallel with Phase 3
5. **Phase 5 (US3 Integration Tests)**: Depends on Phase 2 and Phase 3
6. **Phase 6 (Polish)**: Depends on Phase 2, 3, 4, 5
7. **Phase 7 (Manual Verification)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Authorization Fix)**: MUST complete before any other work - blocks everything
- **US2 (Documentation)**: Can proceed after US1 implementation (T004-T005)
- **US3 (Integration Tests)**: Depends on US1 implementation and unit tests

### Critical Path

1. T001-T003 (Setup) → 2. T004-T005 (Core fix) → 3. T006-T008 (Unit tests) → 4. T009-T021 (Contract tests) → 5. T038 (Full test suite)

### Parallel Opportunities

**After T004-T005 complete**, these can run in parallel:

- **Unit tests**: T006, T007, T008 (different test functions)
- **Contract tests**: T009-T021 (different test files and functions)
- **Documentation**: T022-T024 (different files)
- **Integration tests**: T025-T035 (after unit tests pass)
- **Polish docs**: T036, T037 (different files)

**Example parallel execution for Phase 3**:
```bash
# Launch all unit test tasks together:
Task T006: Add test_credential_get_auth_header_odfhir_format
Task T007: Add test_credential_get_auth_header_uses_secret_values
Task T008: Add test_credential_get_auth_header_no_custom_headers

# Launch all contract test tasks together:
Task T009-T015: Update contract tests for all 6 endpoints
Task T016-T018: Update error scenario tests
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 (Setup - 10 min)
2. Complete Phase 2 (T004-T005 - Core fix - 10 min)
3. Complete Phase 3 (T006-T021 - Test validation - 30 min)
4. Run pytest to verify all tests pass
5. **STOP and VALIDATE**: If tests pass, core fix is complete

### Full Implementation

1. Complete MVP (above) → Authorization fix validated
2. Add Phase 4 (US2 - Documentation - 15 min) → User experience improved
3. Add Phase 5 (US3 - Integration tests - 20 min) → Full coverage validated
4. Add Phase 6 (Polish - 10 min) → Documentation complete
5. Add Phase 7 (Manual verification - 15 min) → Real API validated

### Time Estimates

| Phase | Description | Time |
|-------|-------------|------|
| 1 | Setup & validation | 10 min |
| 2 | Core fix (T004-T005) | 10 min |
| 3 | Test updates (T006-T021) | 30 min |
| 4 | Documentation (T022-T024) | 15 min |
| 5 | Integration tests (T025-T035) | 20 min |
| 6 | Polish (T036-T040) | 10 min |
| 7 | Manual verification (T041-T045) | 15 min |
| **Total** | | **110 min (1.8 hours)** |

---

## Success Criteria

### Code Quality
- ✅ All unit tests pass (tests/unit/)
- ✅ All contract tests pass (tests/contract/)
- ✅ All integration tests pass (tests/integration/)
- ✅ Test coverage ≥90% maintained
- ✅ No new linting or type errors

### Functional Validation
- ✅ get_auth_header() returns single Authorization header
- ✅ Authorization header format: `ODFHIR {key1}/{key2}`
- ✅ No DeveloperKey or CustomerKey headers sent
- ✅ Manual test with real credentials returns 200 OK

### Security & Compliance
- ✅ No PHI logged in any error messages or debug output
- ✅ Authorization header uses SecretStr (not logged)
- ✅ Credentials remain encrypted in OS keyring
- ✅ No plain-text credential storage

### Documentation
- ✅ API contract documentation reflects ODFHIR format
- ✅ README.md explains authentication clearly
- ✅ SECURITY.md documents authorization format
- ✅ CLI prompts clarify "Developer Portal Key"

---

## Rollback Plan

If manual testing (Phase 7) reveals the format is still incorrect:

1. **Quick Rollback**: `git revert` the commit that changed `get_auth_header()` (T004)
2. **Investigation**: Capture actual working Authorization header from OpenDental support or working client
3. **Correction**: Update format string in T004 based on evidence
4. **Re-test**: Run phases 3-7 again with corrected format
5. **Deploy**: Once validated, redeploy with correct format

**Risk**: Low - format is clearly specified by user as `ODFHIR key1/key2`

---

## Notes

- **[P] tasks**: Different files or test functions, can run in parallel
- **[Story] labels**: Map tasks to user stories for traceability
- **Critical dependency**: T004-T005 (core fix) blocks all subsequent work
- **Test-first**: All test tasks (T006-T035) should verify new behavior before manual testing
- **Constitution compliance**: All tests use mocks (no live API calls except Phase 7 manual verification)
- **HIPAA compliance**: Authorization header uses SecretStr, never logged
- **Incremental validation**: Stop after Phase 3 to validate core fix before proceeding to documentation

---

## Validation Checklist

Before marking tasks complete:

- [ ] T004-T005: get_auth_header() returns exactly `{"Authorization": "ODFHIR key1/key2"}`
- [ ] T006-T008: Unit tests verify ODFHIR format and SecretStr usage
- [ ] T009-T021: Contract tests verify Authorization header sent (not DeveloperKey/CustomerKey)
- [ ] T022: CLI prompt says "Developer Portal Key" not "Customer Key"
- [ ] T023-T024: API contract docs show `Authorization: ODFHIR key1/key2` examples
- [ ] T025-T035: Integration tests pass with mocked Authorization header
- [ ] T036-T037: README and SECURITY docs explain ODFHIR format clearly
- [ ] T038: Full test suite passes with ≥90% coverage
- [ ] T039: No PHI logged during any test execution
- [ ] T040: quickstart.md steps work as documented
- [ ] T041-T045: Real API calls return 200 OK (not 401)

**Status**: Ready for implementation  
**Priority**: P0 (Critical - blocks all API functionality)  
**Risk**: Low (focused change, comprehensive test coverage)
