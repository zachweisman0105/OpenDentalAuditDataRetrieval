# Tasks: API Endpoint Testing & Validation

**Feature**: 003-endpoint-testing  
**Status**: Ready to Implement  
**Estimated Time**: 2 hours

---

## Phase 0: Create Test Fixtures (15 min)

- [ ] T001 Create `tests/fixtures/procedurelogs_list.json` with array of procedure records
- [ ] T002 Create `tests/fixtures/allergies_list.json` with array of allergy records
- [ ] T003 Create `tests/fixtures/medicationpats_list.json` with array of medication records
- [ ] T004 Create `tests/fixtures/diseases_list.json` with array of disease records
- [ ] T005 Create `tests/fixtures/patientnotes_dict.json` with single patient notes object
- [ ] T006 Create `tests/fixtures/vitalsigns_list.json` with array of vital signs records
- [ ] T007 Create `tests/fixtures/empty_list.json` with empty array `[]`

**Checkpoint:** All fixtures created with realistic data

---

## Phase 1: Update Existing Contract Tests (30 min)

- [ ] T008 Update `test_fetch_procedure_logs_golden_path` to verify `response.data` is list
- [ ] T009 Update `test_fetch_allergies_golden_path` to verify `response.data` is list
- [ ] T010 Update `test_fetch_medications_golden_path` to verify `response.data` is list
- [ ] T011 Update `test_fetch_problems_golden_path` to verify `response.data` is list
- [ ] T012 Update `test_fetch_patient_notes_golden_path` to verify `response.data` is dict (not list)
- [ ] T013 Update fixtures used in existing tests to match new JSON files

**Checkpoint:** Existing tests updated and passing

---

## Phase 2: Add New Contract Tests (30 min)

### List Response Tests

- [ ] T014 Create `tests/contract/test_api_client_list_responses.py`
- [ ] T015 Add `test_procedurelogs_returns_list_of_dicts` - verify list type
- [ ] T016 Add `test_allergies_returns_list_of_dicts` - verify list type
- [ ] T017 Add `test_medicationpats_returns_list_of_dicts` - verify list type
- [ ] T018 Add `test_diseases_returns_list_of_dicts` - verify list type
- [ ] T019 Add `test_empty_list_response_valid` - verify empty array handled

### Dict Response Tests

- [ ] T020 Create `tests/contract/test_api_client_dict_responses.py`
- [ ] T021 Add `test_patientnotes_returns_dict_not_list` - verify dict type and structure

### VitalSigns Tests

- [ ] T022 Create `tests/contract/test_api_client_vital_signs.py`
- [ ] T023 Add `test_vitalsigns_success_returns_list` - verify PUT with SQL query
- [ ] T024 Add `test_vitalsigns_400_error_handling` - verify error handling

**Checkpoint:** All new contract tests created and passing

---

## Phase 3: Add Integration Tests (30 min)

- [ ] T025 Create `tests/integration/test_endpoint_validation.py`
- [ ] T026 Add `test_orchestration_with_mixed_response_types` - verify all 6 endpoints with list/dict mix
- [ ] T027 Add `test_partial_success_with_vitalsigns_failure` - verify exit code 2 when VitalSigns fails
- [ ] T028 Add `test_empty_lists_handled_correctly` - verify orchestration with empty arrays
- [ ] T029 Add `test_consolidation_accepts_list_responses` - verify ConsolidatedAuditData model
- [ ] T030 Update `tests/integration/test_golden_path.py` to verify response types

**Checkpoint:** Integration tests verify full orchestration

---

## Phase 4: Validation & Documentation (15 min)

- [ ] T031 Run full test suite: `pytest tests/ -v --tb=short`
- [ ] T032 Run contract tests only: `pytest tests/contract/ -v`
- [ ] T033 Run integration tests only: `pytest tests/integration/ -v`
- [ ] T034 Run new list response tests: `pytest tests/contract/test_api_client_list_responses.py -v`
- [ ] T035 Verify test coverage: `pytest --cov=src/opendental_cli --cov-report=term`
- [ ] T036 Update `specs/003-endpoint-testing/research.md` with test results
- [ ] T037 Document any failures or unexpected behavior
- [ ] T038 Mark all tasks complete in this file

**Checkpoint:** All tests passing, coverage 90%+, documentation complete

---

## Bonus Tasks (Optional)

- [ ] T039 Add test for Authorization header still sent correctly with list responses
- [ ] T040 Add test for PHI redaction with list responses
- [ ] T041 Add test for empty dict response (if applicable)
- [ ] T042 Add performance baseline tests for response parsing

---

## Summary

**Total Tasks:** 38 core + 4 bonus = 42 tasks  
**Estimated Time:** 2 hours  
**Current Status:** Ready to implement  

**Critical Path:**
- Phase 0 (Fixtures) → Phase 1 (Update Tests) → Phase 2 (New Tests) → Phase 3 (Integration) → Phase 4 (Validation)

**Success Criteria:**
- All fixtures created with realistic data
- All existing tests updated and passing
- 15+ new tests added for list/dict validation
- Full test suite passes
- Coverage remains 90%+

---

## Quick Start

1. **Start:** Create JSON fixtures in `tests/fixtures/`
2. **Update:** Modify existing contract tests to verify types
3. **Add:** Create new test files for list/dict specific validation
4. **Integrate:** Add orchestration tests with mixed types
5. **Validate:** Run full suite and verify coverage
