# Feature Specification: Fix API Endpoint Parameter Usage

**Feature ID**: `002-fix-endpoint-parameters`  
**Status**: Planning  
**Priority**: P0 - Critical Bug Fix  
**Created**: 2025-12-02

## Problem Statement

After fixing the ODFHIR authorization header format (completed in main branch), testing reveals **only 1 out of 6 endpoints is working correctly**. The root cause is incorrect parameter usage or endpoint formatting for some API calls.

### Current Situation

User reports: "Only 1 endpoint worked" when running `opendental-cli --patnum 39689 --aptnum 99413`

### Root Cause Analysis

Comparing `src/opendental_cli/api_client.py` implementation against `APIEndpoint Data.csv`:

| Endpoint | Current Implementation | CSV Specification | Status |
|----------|----------------------|-------------------|--------|
| **ProcedureLogs** | `GET /procedurelogs?AptNum={aptnum}` | `{AptNum}` parameter | ✅ **CORRECT** |
| **Allergies** | `GET /allergies?PatNum={patnum}` | `{PatNum}` parameter | ✅ **CORRECT** |
| **MedicationPats** | `GET /medicationpats?PatNum={patnum}` | `{PatNum}` parameter | ✅ **CORRECT** |
| **Diseases** | `GET /diseases?PatNum={patnum}` | `{PatNum}` parameter | ✅ **CORRECT** |
| **PatientNotes** | `GET /patientnotes/{patnum}` | "PatNum is required to be in the URL" | ❓ **VERIFY** |
| **VitalSigns** | `PUT /queries/ShortQuery` + SQL | `{AptNum}` in query body | ❓ **VERIFY** |

### Key Issues to Investigate

1. **PatientNotes URL Format**:
   - Current: `/patientnotes/{patnum}` (path parameter)
   - CSV note: "PatNum is required to be in the URL"
   - Ambiguous: Could mean path parameter `/patientnotes/39689` OR query parameter `/patientnotes?PatNum=39689`

2. **VitalSigns Query Structure**:
   - Current: Constructs SQL: `SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum={aptnum}`
   - CSV shows: "Queries PUT ShortQuery" endpoint
   - Needs verification: Table name, column names, query syntax

3. **Unknown Working Endpoint**:
   - Which 1 endpoint is working? Likely ProcedureLogs (first in sequence)
   - Need to test each endpoint individually to identify failures

## User Stories

### US1: Identify Which Endpoints Are Failing (Priority: P0)

**As a** developer  
**I want** to test each endpoint individually with the fixed authorization  
**So that** I can determine which specific endpoints need fixing

**Acceptance Criteria:**
- [ ] Test procedurelogs endpoint with AptNum=99413
- [ ] Test allergies endpoint with PatNum=39689
- [ ] Test medicationpats endpoint with PatNum=39689
- [ ] Test diseases endpoint with PatNum=39689
- [ ] Test patientnotes endpoint with PatNum=39689
- [ ] Test vital_signs endpoint with AptNum=99413
- [ ] Document HTTP status codes and error messages for each
- [ ] Identify which endpoints return 200 OK vs errors

### US2: Fix PatientNotes Endpoint Format (Priority: P0)

**As a** CLI user  
**I want** the PatientNotes endpoint to use the correct URL format  
**So that** I can retrieve medical information successfully

**Acceptance Criteria:**
- [ ] Research/test if endpoint expects path param or query param
- [ ] Try format 1: `GET /patientnotes?PatNum={patnum}`
- [ ] Try format 2: `GET /patientnotes/{patnum}` (current)
- [ ] Update implementation to use correct format
- [ ] Verify endpoint returns 200 OK with valid PatNum
- [ ] Update tests to verify correct format

### US3: Fix VitalSigns Query Endpoint (Priority: P0)

**As a** CLI user  
**I want** the VitalSigns endpoint to construct valid queries  
**So that** I can retrieve vital signs data successfully

**Acceptance Criteria:**
- [ ] Verify SQL query structure for ShortQuery endpoint
- [ ] Confirm table name is `vitalsign` (not `vital_signs`)
- [ ] Confirm column names: DateTaken, Pulse, BP, Height, Weight
- [ ] Test query with AptNum=99413
- [ ] Add error handling for SQL syntax errors
- [ ] Verify endpoint returns 200 OK with valid AptNum

### US4: Add Comprehensive Logging for Debugging (Priority: P1)

**As a** developer  
**I want** detailed logs for each endpoint request/response  
**So that** I can debug API issues quickly

**Acceptance Criteria:**
- [ ] Log full URL for each endpoint (without exposing credentials)
- [ ] Log HTTP status codes and response bodies (redact PHI)
- [ ] Log request parameters (PatNum, AptNum)
- [ ] Add structured logging with endpoint names
- [ ] Preserve Article IV compliance (no real API calls in tests)

## Technical Context

### Current Implementation (api_client.py)

```python
# WORKING (Based on CSV)
async def fetch_procedure_logs(self, aptnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("procedurelogs", f"/procedurelogs?AptNum={aptnum}")

async def fetch_allergies(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("allergies", f"/allergies?PatNum={patnum}")

async def fetch_medications(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("medicationpats", f"/medicationpats?PatNum={patnum}")

async def fetch_problems(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("diseases", f"/diseases?PatNum={patnum}")

# NEEDS VERIFICATION
async def fetch_patient_notes(self, patnum: int) -> EndpointResponse:
    # Current: Path parameter
    return await self.fetch_endpoint("patientnotes", f"/patientnotes/{patnum}")
    # Alternative: Query parameter?
    # return await self.fetch_endpoint("patientnotes", f"/patientnotes?PatNum={patnum}")

async def fetch_vital_signs(self, aptnum: int) -> EndpointResponse:
    # Current: PUT with SQL query
    query_body = {
        "query": f"SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum={aptnum}"
    }
    response = await self._make_request("PUT", "/queries/ShortQuery", json=query_body)
    # Needs verification: table name, column names, WHERE clause syntax
```

### CSV Reference Data

```csv
Target,Method,Endpoint,Parameter,Notes
PatientNotes,GET,/api/v1/patientnotes,{PatNum},"PatNum is required to be in the URL"
VitalSigns,PUT,/api/v1/queries/ShortQuery,{AptNum},"BMI calculation needed: (Weight/Height^2)*703"
```

### Error Patterns to Check

1. **404 Not Found**: Wrong URL path (e.g., path param vs query param)
2. **400 Bad Request**: Malformed query or missing required parameters
3. **401 Unauthorized**: Authorization still broken (unlikely after ODFHIR fix)
4. **500 Server Error**: Backend SQL syntax error (possible in VitalSigns)

## Research Questions

1. ❓ **Which endpoint is the "1 working endpoint"?**
   - Most likely: procedurelogs (first endpoint, simplest format)
   - Need to confirm via individual testing

2. ❓ **PatientNotes URL format?**
   - Path parameter: `/patientnotes/39689` (current)
   - Query parameter: `/patientnotes?PatNum=39689` (alternative)
   - Need to test both formats

3. ❓ **VitalSigns query syntax?**
   - Table name: `vitalsign` vs `vital_signs` vs `VitalSigns`
   - Column names: Case-sensitive?
   - WHERE clause: `AptNum={aptnum}` vs `AptNum = {aptnum}`

4. ❓ **Are there API versioning differences?**
   - CSV shows: `https://api.opendental.com/api/v1/...`
   - Implementation uses: `self.base_url` (from credentials)
   - Need to verify base_url includes `/api/v1`

## Success Metrics

- **Primary**: All 6 endpoints return 200 OK with valid PatNum/AptNum
- **Secondary**: CLI successfully retrieves complete data: `opendental-cli --patnum 39689 --aptnum 99413` exits with code 0
- **Testing**: Integration tests pass for all endpoints with mocked responses

## Dependencies

- ✅ ODFHIR authorization fix (completed in previous feature)
- ⏳ Access to OpenDental API for testing (or detailed documentation)
- ⏳ Valid PatNum (39689) and AptNum (99413) values for testing

## Out of Scope

- Adding new endpoints beyond the 6 specified
- Modifying authentication mechanism
- Adding BMI calculation for vital signs (CSV mentions it, but not in current scope)
- Performance optimization
- Pagination support

## Timeline Estimate

- Phase 0 (Research & Individual Testing): 30 minutes
- Phase 1 (Fix PatientNotes): 15 minutes
- Phase 2 (Fix VitalSigns): 15 minutes
- Phase 3 (Testing & Validation): 30 minutes
- Phase 4 (Documentation): 15 minutes
- **Total**: ~1.75 hours

## Next Steps

1. Create research.md with endpoint testing matrix
2. Test each endpoint individually to identify failures
3. Create data-model.md documenting expected request/response formats
4. Generate implementation plan in plan.md
5. Create task breakdown in tasks.md
