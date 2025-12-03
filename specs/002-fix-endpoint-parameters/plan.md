# Implementation Plan: Fix API Endpoint Parameter Usage

**Feature**: 002-fix-endpoint-parameters  
**Date**: 2025-12-02  
**Estimated Time**: 1.75 hours

## Overview

Fix API endpoint parameter formatting issues identified after ODFHIR authorization fix. Research indicates PatientNotes and VitalSigns endpoints may have incorrect URL formats or query structures.

## Prerequisites

- ✅ ODFHIR authorization fix completed (specs/main/)
- ✅ Authorization header now sends: `Authorization: ODFHIR {key1}/{key2}`
- ⏳ Valid test credentials with PatNum=39689, AptNum=99413
- ⏳ CSV analysis complete (see research.md)

---

## Phase 0: Diagnostic Testing (30 minutes)

**Goal:** Identify which specific endpoints are failing and capture error details

### Tasks

**T001: Add Individual Endpoint Testing Script**
- Create `scripts/test_individual_endpoints.py`
- Test each endpoint independently
- Log HTTP status, response body, and timing
- No PHI in logs (Article IV compliance)

**T002: Run Diagnostic Tests**
- Test with PatNum=39689, AptNum=99413
- Capture results matrix:

| Endpoint | Status | Response | Notes |
|----------|--------|----------|-------|
| ProcedureLogs | ? | | |
| Allergies | ? | | |
| MedicationPats | ? | | |
| Diseases | ? | | |
| PatientNotes | ? | | |
| VitalSigns | ? | | |

**T003: Document Findings in research.md**
- Update research.md with actual test results
- Identify failing endpoints
- Capture error messages for troubleshooting

**Checkpoint:** Know exactly which endpoints need fixing

---

## Phase 1: Fix PatientNotes Endpoint (15 minutes)

**Precondition:** T002 diagnostic test shows PatientNotes endpoint failing

### Option A: If 404 Not Found (Path Parameter Issue)

**T004: Switch PatientNotes to Query Parameter**

Update `src/opendental_cli/api_client.py`:
```python
# BEFORE (path parameter)
async def fetch_patient_notes(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("patientnotes", f"/patientnotes/{patnum}")

# AFTER (query parameter)
async def fetch_patient_notes(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("patientnotes", f"/patientnotes?PatNum={patnum}")
```

**T005: Update Tests**
- Update contract tests in `tests/contract/test_api_client_golden_path.py`
- Verify mock expects query parameter format
- Update integration tests if needed

### Option B: If 200 OK (Path Parameter Correct)

**T004-ALT: No change needed, document in research.md**
- Confirm path parameter format is correct
- Update research.md with confirmation

**Checkpoint:** PatientNotes endpoint returns 200 OK

---

## Phase 2: Fix VitalSigns Endpoint (15 minutes)

**Precondition:** T002 diagnostic test shows VitalSigns endpoint failing

### Option A: If 400/500 Error (SQL Syntax Issue)

**T006: Update VitalSigns Query Structure**

Possible fixes based on error message:

**Fix 1: Table Name**
```python
# Try different table name variations
query_body = {
    "query": f"SELECT DateTaken, Pulse, BP, Height, Weight FROM vital_signs WHERE AptNum={aptnum}"  # plural
}
```

**Fix 2: Column Names (Case Sensitivity)**
```python
# Try lowercase columns
query_body = {
    "query": f"SELECT datetaken, pulse, bp, height, weight FROM vitalsign WHERE aptnum={aptnum}"
}
```

**Fix 3: WHERE Clause Spacing**
```python
# Add spaces around equals
query_body = {
    "query": f"SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum = {aptnum}"
}
```

**T007: Add Query Logging (PHI-Safe)**
- Log constructed SQL query (without results)
- Log HTTP status and error message
- Help future debugging without exposing PHI

**T008: Update Tests**
- Update `tests/contract/test_api_client_golden_path.py`
- Update mock to expect correct query format
- Add test for SQL syntax validation

### Option B: If 200 OK (Query Correct)

**T006-ALT: No change needed, document in research.md**

**Checkpoint:** VitalSigns endpoint returns 200 OK

---

## Phase 3: Verify Base URL Configuration (10 minutes)

**T009: Check Credential Base URL**

Verify stored credentials include `/api/v1`:
```python
# Should be: https://api.opendental.com/api/v1
# Not: https://api.opendental.com
```

**If base URL missing /api/v1:**

**T010: Add Base URL Validation**

Option A - Update credential prompt:
```python
# cli.py
base_url = click.prompt(
    "API Base URL (e.g., https://api.example.com/api/v1)",
    type=str
)
```

Option B - Auto-append version:
```python
# api_client.py
def __init__(self, credential: APICredential):
    base = str(credential.base_url).rstrip("/")
    if not base.endswith("/api/v1"):
        base = f"{base}/api/v1"
    self.base_url = base
```

**Checkpoint:** All endpoints use correct base URL

---

## Phase 4: Integration Testing (30 minutes)

**T011: Update Contract Tests**

Update `tests/contract/test_api_client_golden_path.py`:
- Verify each endpoint uses correct URL format
- Update respx mocks for PatientNotes (if changed)
- Update respx mocks for VitalSigns (if changed)
- Ensure all 6 tests pass

**T012: Update Integration Tests**

Update `tests/integration/test_golden_path.py`:
- Test full orchestration with all 6 endpoints
- Verify exit code 0 (all succeed)
- Check response structure matches CSV examples

**T013: Run Full Test Suite**
```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass, no regressions

**Checkpoint:** Test suite passes with 90%+ coverage

---

## Phase 5: Documentation Updates (15 minutes)

**T014: Update API Contract Documentation**

Update `specs/001-audit-data-cli/contracts/opendental-api.md`:
- Document PatientNotes URL format (path vs query parameter)
- Document VitalSigns SQL query structure
- Add notes about base URL `/api/v1` requirement

**T015: Update research.md**
- Document final endpoint formats (confirmed working)
- Record test results from Phase 0
- Document any API quirks discovered

**T016: Update README.md**
- Add troubleshooting section
- Document common endpoint errors
- Explain base URL configuration

**Checkpoint:** Documentation accurate and complete

---

## Phase 6: Manual Verification (Optional, 10 minutes)

**Only if user has access to real OpenDental API**

**T017: Test with Real API**
```bash
opendental-cli --patnum 39689 --aptnum 99413 --output-file test_output.json
```

Expected:
- Exit code 0
- All 6 endpoints successful
- JSON output contains data from all endpoints

**T018: Verify Output Structure**
- Check JSON has keys: procedurelogs, allergies, medicationpats, diseases, patientnotes, vital_signs
- Verify data structure matches CSV examples
- Confirm no PHI in logs (audit.log)

**Checkpoint:** CLI works end-to-end with real API

---

## Rollback Plan

If changes break existing functionality:

1. **Revert api_client.py** to previous version:
   ```bash
   git checkout HEAD~1 src/opendental_cli/api_client.py
   ```

2. **Re-run tests** to confirm revert successful:
   ```bash
   pytest tests/contract/ -v
   ```

3. **Investigate** error messages more carefully before re-attempting fix

---

## Success Criteria

- [ ] All 6 endpoints return 200 OK with valid credentials
- [ ] Test suite passes with no regressions
- [ ] CLI successfully retrieves data: `opendental-cli --patnum 39689 --aptnum 99413`
- [ ] Exit code 0 (all endpoints successful)
- [ ] Documentation updated with correct endpoint formats
- [ ] No PHI in logs or error messages

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PatientNotes uses non-standard format | Medium | Medium | Test both path and query param formats |
| VitalSigns SQL syntax varies by DB version | Medium | High | Capture error messages, check docs |
| Base URL missing /api/v1 | Low | Critical | Add validation and auto-correction |
| Breaking existing working endpoints | Low | High | Run full test suite before/after changes |

---

## Dependencies

- Access to OpenDental API documentation (helpful but not required)
- Valid test credentials (PatNum=39689, AptNum=99413)
- Pytest and respx for testing

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0: Diagnostic Testing | 30 min | Valid credentials |
| Phase 1: Fix PatientNotes | 15 min | Phase 0 results |
| Phase 2: Fix VitalSigns | 15 min | Phase 0 results |
| Phase 3: Verify Base URL | 10 min | Phase 0 results |
| Phase 4: Integration Testing | 30 min | Phases 1-3 complete |
| Phase 5: Documentation | 15 min | Phases 1-4 complete |
| Phase 6: Manual Verification | 10 min | Real API access (optional) |
| **Total** | **1 hour 55 min** | |

**Critical Path:** Phase 0 → Phase 1 or 2 (whichever fails) → Phase 4

---

## Notes

- **Article IV Compliance**: All tests use mocked responses, no real API calls in test suite
- **PHI Protection**: Error messages and logs must not contain PatNum, names, DOBs, etc.
- **Backward Compatibility**: Changes should not break existing credential storage or CLI usage
