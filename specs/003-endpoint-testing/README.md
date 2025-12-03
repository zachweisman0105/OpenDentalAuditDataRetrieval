# Feature 003: API Endpoint Testing & Validation

**Status:** ✅ Planning Complete - Ready for Implementation  
**Branch:** Will be created during implementation  
**Estimated Time:** 2 hours  
**Created:** 2025-01-26

---

## Executive Summary

This feature implements comprehensive testing to validate that all 6 OpenDental FHIR API endpoints work correctly after fixing the data type handling issue. The recent fix changed `EndpointResponse.data` from accepting only `dict` to accepting `dict | list`, which resolves Pydantic validation errors that were causing 4/5 endpoints to fail.

**Problem Solved:**
- API returns arrays (lists) for collection endpoints
- Previous model only accepted dictionaries
- Caused validation errors: `Input should be a valid dictionary [type=dict_type, input_value=[{...}], input_type=list]`

**Solution:**
- Update `EndpointResponse.data` type to `dict | list`
- Create comprehensive test suite to validate fix
- Verify all 6 endpoints work correctly with proper type handling

---

## Planning Artifacts

### Core Documentation

1. **spec.md** - Feature specification with 4 user stories
   - US1: Verify collection endpoints return lists
   - US2: Verify PatientNotes returns dict
   - US3: Validate VitalSigns query
   - US4: Integration test all endpoints

2. **research.md** - Technical analysis
   - Documents two response patterns (list vs dict)
   - Complete response specifications for all 6 endpoints
   - Defines 7 JSON fixture requirements
   - Test validation strategies

3. **plan.md** - Implementation plan
   - Phase 0: Create 7 JSON fixtures (15 min)
   - Phase 1: Update 6 existing tests (30 min)
   - Phase 2: Add new contract tests (30 min)
   - Phase 3: Add integration tests (30 min)
   - Phase 4: Validate and document (15 min)

4. **data-model.md** - Data structure definitions
   - 6 fixture item models
   - Updated response wrapper models
   - Test assertion models
   - Response type mapping table

5. **tasks.md** - Task breakdown
   - 38 core tasks + 4 bonus = 42 total tasks
   - Organized into 4 phases
   - Clear checkpoints and success criteria

6. **quickstart.md** - Quick start guide
   - Immediate action steps
   - Test matrix with status
   - Common issues and fixes
   - Success checklist

7. **contracts/test-contracts.md** - Test contracts
   - 6 contract definitions
   - Type and structure validation rules
   - Breaking change documentation
   - Test coverage matrix

---

## Implementation Roadmap

### Phase 0: Create Test Fixtures (15 min)

**Tasks:** T001-T007

Create JSON fixture files in `tests/fixtures/`:
- `procedurelogs_list.json` - Array of procedure log records
- `allergies_list.json` - Array of allergy records
- `medicationpats_list.json` - Array of medication records
- `diseases_list.json` - Array of disease records
- `patientnotes_dict.json` - Single patient notes object
- `vitalsigns_list.json` - Array of vital signs records
- `empty_list.json` - Empty array for edge cases

**Success Criteria:**
- All 7 fixtures created
- Match actual API response structure
- No PHI in fixture data
- Valid JSON format

### Phase 1: Update Existing Tests (30 min)

**Tasks:** T008-T013

Update `tests/contract/test_api_client_golden_path.py`:
- Add `assert isinstance(response.data, list)` to collection endpoint tests
- Add `assert isinstance(response.data, dict)` to PatientNotes test
- Verify all existing tests pass with new fixtures

**Success Criteria:**
- All 6 existing tests updated
- All tests pass
- No Pydantic validation errors

### Phase 2: Add New Contract Tests (30 min)

**Tasks:** T014-T024

Create new test files:
- `test_api_client_list_responses.py` - 5 tests for list handling
- `test_api_client_dict_responses.py` - 1 test for dict handling
- `test_api_client_vital_signs.py` - 2 tests for VitalSigns query

**Success Criteria:**
- 10+ new tests created
- All tests pass
- Edge cases covered (empty list, errors)

### Phase 3: Add Integration Tests (30 min)

**Tasks:** T025-T030

Create and update integration tests:
- `test_endpoint_validation.py` - Mixed type orchestration
- Update `test_golden_path.py` - Type verification
- Test partial success scenarios

**Success Criteria:**
- 3+ integration tests added
- Full orchestration validated
- Exit code handling tested

### Phase 4: Validation & Documentation (15 min)

**Tasks:** T031-T038

Run tests and document results:
- Run full test suite
- Verify coverage 90%+
- Update research.md with results
- Mark all tasks complete

**Success Criteria:**
- All tests passing
- Coverage maintained
- Documentation updated
- Feature complete

---

## Technical Context

### API Response Patterns

**Collection Endpoints (Return Lists):**
- ProcedureLogs: `GET /fhir/v1/procedurelogs?PatientNum={id}` → `[{...}, {...}]`
- Allergies: `GET /fhir/v1/allergies?PatientNum={id}` → `[{...}, {...}]`
- MedicationPats: `GET /fhir/v1/medicationpats?PatientNum={id}` → `[{...}, {...}]`
- Diseases: `GET /fhir/v1/diseases?PatientNum={id}` → `[{...}, {...}]`

**Single Resource Endpoint (Returns Dict):**
- PatientNotes: `GET /fhir/v1/patientnotes?PatientNum={id}` → `{...}`

**Query Endpoint (Returns List):**
- VitalSigns: `PUT /fhir/v1/vitals?PatientNum={id}` + SQL query → `[{...}, {...}]`

### Data Model Fix

**Before (BROKEN):**
```python
class EndpointResponse(BaseModel):
    success: bool = True
    data: dict[str, Any] | None = None  # Only accepts dict
    error: str | None = None
```

**After (FIXED):**
```python
class EndpointResponse(BaseModel):
    success: bool = True
    data: dict[str, Any] | list[dict[str, Any]] | None = None  # Accepts dict OR list
    error: str | None = None
```

### Test Stack

- **pytest 7.4+** - Testing framework
- **pytest-asyncio 0.21+** - Async test support
- **respx 0.20+** - HTTP mocking (Article IV compliance)
- **pydantic 2.5+** - Data validation

---

## Success Metrics

### Test Coverage

- **Target:** 90%+ code coverage maintained
- **New Tests:** 15+ tests added
- **Test Types:** Unit, contract, integration

### Endpoint Validation

- **Expected Working:** 5/6 endpoints (all except VitalSigns)
- **ProcedureLogs:** ✅ Should return list, validate correctly
- **Allergies:** ✅ Should return list, validate correctly
- **MedicationPats:** ✅ Should return list, validate correctly
- **Diseases:** ✅ Should return list, validate correctly
- **PatientNotes:** ✅ Should return dict, validate correctly
- **VitalSigns:** ⚠️ May still return 400 error (SQL query issue)

### Exit Codes

- **Exit 0:** All endpoints successful (if VitalSigns fixed)
- **Exit 2:** Partial success - 5/6 working, VitalSigns fails (expected)

---

## Risk Assessment

### Low Risk

- ✅ Fix already applied and tested manually
- ✅ Type union well-supported by Pydantic
- ✅ Backward compatible (dict still accepted)
- ✅ No changes to API calls or authentication

### Medium Risk

- ⚠️ VitalSigns still returns 400 error (SQL query issue)
- ⚠️ Unknown if any edge cases exist (empty arrays, nulls)

### Mitigation

- Create comprehensive test fixtures
- Test empty response scenarios
- Document known VitalSigns issue
- Add error handling tests

---

## Dependencies

### Internal

- `src/opendental_cli/models/response.py` - Data model with fix
- `src/opendental_cli/api_client.py` - API client methods
- `tests/contract/test_api_client_golden_path.py` - Existing tests

### External

- OpenDental FHIR API - Must be accessible (or mocked)
- Python 3.11+ - Type union syntax
- Pydantic 2.5+ - Type validation

### Assumptions

1. API returns consistent response formats
2. Collection endpoints always return arrays
3. PatientNotes always returns single object
4. Empty arrays are valid responses
5. VitalSigns may continue to fail with 400 error

---

## Constitution Check

### Article IV Compliance ✅

**Requirement:** No automated systems shall query production PHI

**Compliance:**
- All tests use respx mocking
- No real API calls in test suite
- Fixtures use placeholder data only
- No actual patient data required

### Gate: Exit Code 0 Required ❌ (Waived)

**Status:** Will likely exit code 2 (partial success)

**Justification:**
- VitalSigns has known 400 error
- 5/6 endpoints working is acceptable
- VitalSigns issue separate from dict/list fix
- Can be resolved in future feature

---

## Next Steps

1. **Run Implementation:**
   ```bash
   # From repo root
   cd specs/003-endpoint-testing
   # Follow quickstart.md instructions
   ```

2. **Create Branch:**
   ```bash
   git checkout -b feature/003-endpoint-testing
   ```

3. **Phase 0: Create Fixtures (15 min)**
   - Start with procedurelogs_list.json
   - Follow fixture specifications in data-model.md

4. **Phase 1: Update Tests (30 min)**
   - Add type assertions to existing tests
   - Verify tests pass

5. **Phase 2-4: Complete Implementation (1h 15min)**
   - Follow plan.md task sequence
   - Run tests after each phase

---

## Related Features

- **specs/main/** - ODFHIR authorization fix (✅ Complete)
- **specs/002-fix-endpoint-parameters/** - Endpoint diagnostic (✅ Fix applied)
- **Future:** VitalSigns SQL query fix (⏳ Deferred)

---

## Documentation Status

| Document | Status | Location |
|----------|--------|----------|
| Feature Spec | ✅ Complete | spec.md |
| Research | ✅ Complete | research.md |
| Implementation Plan | ✅ Complete | plan.md |
| Data Model | ✅ Complete | data-model.md |
| Tasks | ✅ Complete | tasks.md |
| Quick Start | ✅ Complete | quickstart.md |
| Contracts | ✅ Complete | contracts/test-contracts.md |

---

## Approval

**Planning Phase:** ✅ Complete  
**Ready for Implementation:** ✅ Yes  
**Estimated Completion:** 2 hours from start  
**Risk Level:** Low-Medium  

**Proceed to implementation phase following quickstart.md instructions.**
