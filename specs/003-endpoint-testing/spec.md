# Feature Specification: API Endpoint Testing & Validation

**Feature ID**: `003-endpoint-testing`  
**Status**: Planning  
**Priority**: P1 - Critical for Validation  
**Created**: 2025-12-02

## Problem Statement

After fixing the data type validation issue (dict vs list), we need comprehensive tests to:
1. Verify all 5 working endpoints return correct data structures
2. Ensure the fixed `EndpointResponse` model handles both dict and list responses
3. Validate VitalSigns endpoint behavior (currently returning 400)
4. Prevent future regressions with automated testing

## Context

**Previous Fix (specs/002-fix-endpoint-parameters):**
- Changed `EndpointResponse.data` from `dict` to `dict | list`
- Fixed 4 endpoints that were failing with Pydantic validation errors
- Result: 5/6 endpoints should now work (VitalSigns still has 400 error)

**Current State:**
- ProcedureLogs: Returns list ✅ (should work now)
- Allergies: Returns list ✅ (should work now)
- MedicationPats: Returns list ✅ (should work now)
- Diseases: Returns list ✅ (should work now)
- PatientNotes: Returns dict ✅ (was already working)
- VitalSigns: Returns 400 ❌ (SQL query issue)

## User Stories

### US1: Verify Collection Endpoints Return Lists (Priority: P0)

**As a** developer  
**I want** tests that verify procedurelogs, allergies, medicationpats, and diseases endpoints return list responses  
**So that** I can confirm the dict|list type fix works correctly

**Acceptance Criteria:**
- [ ] Test procedurelogs endpoint returns `list[dict]`
- [ ] Test allergies endpoint returns `list[dict]`
- [ ] Test medicationpats endpoint returns `list[dict]`
- [ ] Test diseases endpoint returns `list[dict]`
- [ ] Verify EndpointResponse.success = True for 200 responses
- [ ] Verify data field contains expected structure
- [ ] All tests use respx mocking (no real API calls)

### US2: Verify Single Resource Endpoint Returns Dict (Priority: P0)

**As a** developer  
**I want** tests that verify patientnotes endpoint returns dict response  
**So that** I can confirm single resource handling still works

**Acceptance Criteria:**
- [ ] Test patientnotes endpoint returns `dict`
- [ ] Verify endpoint uses path parameter: `/patientnotes/{patnum}`
- [ ] Verify response structure matches CSV specification
- [ ] Test uses respx mocking (no real API calls)

### US3: Validate VitalSigns Query Endpoint (Priority: P1)

**As a** developer  
**I want** tests for the VitalSigns ShortQuery endpoint  
**So that** I can identify and fix the 400 error

**Acceptance Criteria:**
- [ ] Test VitalSigns with current query format
- [ ] Test alternative query formats if 400 persists
- [ ] Verify PUT method with JSON body
- [ ] Document working query format
- [ ] Test uses respx mocking (no real API calls)

### US4: Integration Test with All Endpoints (Priority: P1)

**As a** developer  
**I want** an integration test that calls all 6 endpoints  
**So that** I can verify the full orchestration works end-to-end

**Acceptance Criteria:**
- [ ] Test orchestrate_retrieval with all endpoints
- [ ] Verify 5/6 endpoints succeed (or 6/6 if VitalSigns fixed)
- [ ] Verify ConsolidatedAuditData contains success dict
- [ ] Verify failures list contains VitalSigns if still broken
- [ ] Test exit code logic (0 = all success, 1 = all fail, 2 = partial)
- [ ] Test uses respx mocking (no real API calls)

## Technical Approach

### Test Structure

```
tests/
├── contract/
│   ├── test_api_client_golden_path.py       # Update existing
│   ├── test_api_client_list_responses.py    # NEW - test list handling
│   └── test_api_client_vital_signs.py       # NEW - VitalSigns testing
├── integration/
│   ├── test_golden_path.py                  # Update existing
│   └── test_endpoint_validation.py          # NEW - full validation
└── fixtures/
    ├── procedurelogs_list.json              # NEW
    ├── allergies_list.json                  # NEW
    ├── medicationpats_list.json             # NEW
    ├── diseases_list.json                   # NEW
    └── vitalsigns_success.json              # NEW
```

### Test Fixtures

Create realistic JSON fixtures matching CSV examples:

**procedurelogs_list.json:**
```json
[
  {
    "ProcCode": "D0220",
    "Descript": "intraoral - periapical first radiographic image",
    "ProcFee": "31.00",
    "ProcStatus": "TP"
  }
]
```

**patientnotes_dict.json** (already exists as patient_12345.json):
```json
{
  "PatNum": 39689,
  "MedicalComp": "Test TestTestTestTestTestTestTestTestTest",
  "ICEName": "",
  "ICEPhone": ""
}
```

### Test Cases

#### Contract Tests (Unit-level)

1. **test_procedurelogs_returns_list**: Verify response.data is list
2. **test_allergies_returns_list**: Verify response.data is list
3. **test_medicationpats_returns_list**: Verify response.data is list
4. **test_diseases_returns_list**: Verify response.data is list
5. **test_patientnotes_returns_dict**: Verify response.data is dict
6. **test_vitalsigns_query_format**: Test PUT with SQL query body

#### Integration Tests

1. **test_all_endpoints_with_mixed_types**: Verify orchestration handles both list and dict
2. **test_consolidation_with_list_responses**: Verify ConsolidatedAuditData accepts lists
3. **test_partial_success_with_vitalsigns_failure**: Verify exit code 2 when VitalSigns fails

### Validation Rules

Each test should verify:
- HTTP status code (200 for success)
- EndpointResponse.success boolean
- EndpointResponse.data type (list or dict)
- Data structure matches CSV specification
- No PHI exposure in logs or errors

## Success Metrics

- [ ] All existing tests still pass
- [ ] New tests cover list response handling
- [ ] New tests cover dict response handling
- [ ] Integration tests verify full orchestration
- [ ] Test coverage remains 90%+
- [ ] All tests use mocked responses (Article IV compliance)

## Dependencies

- ✅ specs/002-fix-endpoint-parameters (data type fix applied)
- respx library for HTTP mocking
- pytest and pytest-asyncio
- JSON fixtures matching API responses

## Out of Scope

- Testing with real API credentials (all tests use mocks)
- Performance testing
- Load testing
- Testing other HTTP methods (GET/PUT already covered)

## Timeline Estimate

- Phase 0 (Setup): Create JSON fixtures - 15 min
- Phase 1 (Contract Tests): Update and add contract tests - 30 min
- Phase 2 (Integration Tests): Add integration tests - 30 min
- Phase 3 (Validation): Run full suite and verify - 15 min
- **Total**: ~1.5 hours

## Technical Context

### Current EndpointResponse Model (Fixed)

```python
class EndpointResponse(BaseModel):
    data: dict[str, Any] | list[dict[str, Any]] | None
```

### API Response Patterns

**Collection Endpoints (return list):**
- ProcedureLogs: `GET /procedurelogs?AptNum={aptnum}`
- Allergies: `GET /allergies?PatNum={patnum}`
- MedicationPats: `GET /medicationpats?PatNum={patnum}`
- Diseases: `GET /diseases?PatNum={patnum}`

**Single Resource Endpoint (returns dict):**
- PatientNotes: `GET /patientnotes/{patnum}`

**Query Endpoint (special case):**
- VitalSigns: `PUT /queries/ShortQuery` (body: SQL query)

## Open Questions

1. ❓ Should we add tests for empty list responses (patient has no allergies, etc.)?
2. ❓ Should we test error cases (404, 401, 500) with both list and dict expectations?
3. ❓ Do we need separate tests for Authorization header with list/dict responses?
4. ❓ Should VitalSigns tests assume 400 error or try to fix and test success?

## Next Steps

1. Create JSON fixtures for list responses
2. Update existing contract tests to verify response types
3. Add new contract tests for list-specific validation
4. Add integration tests for mixed dict/list handling
5. Run full test suite and verify coverage
