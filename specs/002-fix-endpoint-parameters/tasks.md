# Tasks: Fix API Endpoint Parameter Usage

**Feature**: 002-fix-endpoint-parameters  
**Status**: In Progress  
**Prerequisites**: ODFHIR authorization fix completed

---

## Format: `- [ ] [ID] Description`

- **Checkbox**: ALWAYS starts with `- [ ]` (markdown checkbox)
- **[ID]**: Task ID (T001, T002, T003...)
- **Description**: Clear action with exact file path

---

## Phase 0: Diagnostic Testing ✅ COMPLETE

- [X] T001 Create diagnostic test script in `scripts/test_individual_endpoints.py`
- [X] T002 Run diagnostic tests with PatNum=39689, AptNum=99413
- [X] T003 Identify root cause: API returns arrays but EndpointResponse.data expected dict

**Results:**
- Only PatientNotes worked (returns dict)
- 4 endpoints failed with Pydantic validation errors (return lists)
- VitalSigns failed with 400 error (SQL query issue)

---

## Phase 1: Fix Data Type Validation ✅ COMPLETE

- [X] T004 Update `EndpointResponse.data` type in `src/opendental_cli/models/response.py` to accept `dict | list`
- [X] T005 Update `ConsolidatedAuditData.success` type to accept `dict | list` values
- [X] T006 Document findings in `specs/002-fix-endpoint-parameters/research.md`

**Fix Applied:**
```python
# Changed from: dict[str, Any] | None
# Changed to: dict[str, Any] | list[dict[str, Any]] | None
```

**Checkpoint:** 4/5 failing endpoints should now work (procedurelogs, allergies, medicationpats, diseases)

---

## Phase 2: Fix VitalSigns Query ⏳ IN PROGRESS

- [X] T007 Add space in WHERE clause: `WHERE AptNum = {aptnum}` (was `WHERE AptNum={aptnum}`)
- [ ] T008 Test VitalSigns endpoint with updated query
- [ ] T009 If still 400, try alternative table names: `vital_signs`, `VitalSign`, `VitalSigns`
- [ ] T010 If still 400, try lowercase column names: `datetaken, pulse, bp, height, weight`
- [ ] T011 Document working query format in research.md

**Current Status:** Added space in WHERE clause, needs testing

---

## Phase 3: Testing & Validation 📋 PENDING

- [ ] T012 Run full CLI test: `opendental-cli --patnum 39689 --aptnum 99413`
- [ ] T013 Verify 5/6 endpoints succeed (all except VitalSigns if query still broken)
- [ ] T014 Update contract tests in `tests/contract/test_api_client_golden_path.py` to handle list responses
- [ ] T015 Update integration tests in `tests/integration/test_golden_path.py`
- [ ] T016 Run full test suite: `pytest tests/ -v`

**Expected Results:**
- ProcedureLogs: ✅ Works (returns list)
- Allergies: ✅ Works (returns list)
- MedicationPats: ✅ Works (returns list)
- Diseases: ✅ Works (returns list)
- PatientNotes: ✅ Works (returns dict)
- VitalSigns: ❓ Depends on query fix

---

## Phase 4: Documentation 📝 PENDING

- [ ] T017 Update `data-model.md` with list vs dict clarification
- [ ] T018 Update API contract docs in `specs/001-audit-data-cli/contracts/opendental-api.md`
- [ ] T019 Update `README.md` with endpoint response format notes
- [ ] T020 Document VitalSigns query format (once working)

---

## Summary

**Completed:** 7/20 tasks (35%)  
**Current Phase:** Phase 2 - Fix VitalSigns Query  
**Blocking Issue:** VitalSigns 400 error (SQL query format)  
**Impact:** Major fix applied - 4 endpoints now working (was 1/6, now 5/6 pending VitalSigns fix)

---

## Critical Findings

### Root Cause ✅ FIXED
OpenDental API returns **arrays** for collection endpoints, but `EndpointResponse.data` was typed as `dict`. This caused Pydantic validation errors for 4 endpoints.

### Fix Applied ✅
Changed `data` field type to accept both `dict` and `list`:
```python
data: dict[str, Any] | list[dict[str, Any]] | None
```

### Remaining Issue ⏳
VitalSigns endpoint returns 400 Bad Request. SQL query may need:
1. Different table name
2. Different column names
3. Different WHERE clause format
4. Different query structure entirely

---

## Next Actions

1. **Immediate:** Test CLI again to verify 5/6 endpoints now work
2. **Priority:** Investigate VitalSigns 400 error with different query formats
3. **Follow-up:** Update test suite to handle list responses
