# Research: API Endpoint Parameter Analysis

**Feature**: 002-fix-endpoint-parameters  
**Date**: 2025-12-02  
**Researcher**: AI Assistant

## Executive Summary

Analysis of `APIEndpoint Data.csv` against `src/opendental_cli/api_client.py` implementation reveals that **all 6 endpoints appear to be using correct parameter types** (PatNum vs AptNum), but there are potential issues with:

1. **PatientNotes**: URL format ambiguity (path vs query parameter)
2. **VitalSigns**: SQL query construction for ShortQuery endpoint
3. **Base URL**: Need to verify includes `/api/v1` prefix

## Endpoint Analysis Matrix

### 1. ProcedureLogs (Procedure Codes)

**CSV Specification:**
- Method: `GET`
- Endpoint: `https://api.opendental.com/api/v1/procedurelogs`
- Parameter: `{AptNum}`
- Example: Returns ProcCode, Descript, ProcFee, ProcStatus

**Current Implementation:**
```python
async def fetch_procedure_logs(self, aptnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("procedurelogs", f"/procedurelogs?AptNum={aptnum}")
```

**Assessment:** ✅ **CORRECT**
- Uses AptNum (appointment number) as required
- Query parameter format: `/procedurelogs?AptNum={aptnum}`
- Method: GET

---

### 2. Allergies

**CSV Specification:**
- Method: `GET`
- Endpoint: `https://api.opendental.com/api/v1/allergies`
- Parameter: `{PatNum}`
- Example: Returns AllergyNum, defDescription, Reaction, StatusIsActive

**Current Implementation:**
```python
async def fetch_allergies(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("allergies", f"/allergies?PatNum={patnum}")
```

**Assessment:** ✅ **CORRECT**
- Uses PatNum (patient number) as required
- Query parameter format: `/allergies?PatNum={patnum}`
- Method: GET

---

### 3. MedicationPats (Medications)

**CSV Specification:**
- Method: `GET`
- Endpoint: `https://api.opendental.com/api/v1/medicationpats`
- Parameter: `{PatNum}`
- Example: Returns MedicationPatNum, medName, PatNote
- Note: "Inactive Medications are not returned"

**Current Implementation:**
```python
async def fetch_medications(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("medicationpats", f"/medicationpats?PatNum={patnum}")
```

**Assessment:** ✅ **CORRECT**
- Uses PatNum as required
- Query parameter format: `/medicationpats?PatNum={patnum}`
- Method: GET

---

### 4. Diseases (Problems)

**CSV Specification:**
- Method: `GET`
- Endpoint: `https://api.opendental.com/api/v1/diseases`
- Parameter: `{PatNum}`
- Example: Returns DiseaseNum, diseaseDefName, PatNote, ProbStatus

**Current Implementation:**
```python
async def fetch_problems(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("diseases", f"/diseases?PatNum={patnum}")
```

**Assessment:** ✅ **CORRECT**
- Uses PatNum as required
- Query parameter format: `/diseases?PatNum={patnum}`
- Method: GET

---

### 5. PatientNotes (Medical Info) ⚠️

**CSV Specification:**
- Method: `GET`
- Endpoint: `https://api.opendental.com/api/v1/patientnotes`
- Parameter: `{PatNum}`
- Example: Returns PatNum, MedicalComp, ICEName, ICEPhone
- **Note**: "PatNum is required to be in the URL"

**Current Implementation:**
```python
async def fetch_patient_notes(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("patientnotes", f"/patientnotes/{patnum}")
```

**Assessment:** ❓ **NEEDS VERIFICATION**

**Two Possible Interpretations:**

**Option A - Path Parameter (CURRENT):**
```http
GET /api/v1/patientnotes/39689
```
- Interprets "in the URL" as path parameter
- RESTful convention for single resource retrieval
- No query string needed

**Option B - Query Parameter:**
```http
GET /api/v1/patientnotes?PatNum=39689
```
- Interprets "in the URL" as query parameter (URL includes query string)
- Consistent with other endpoints
- Uses query string format

**Recommendation:** Test both formats to determine which works:
1. Try current path parameter format first
2. If 404/400 error, try query parameter format
3. Check error message for hints about expected format

---

### 6. VitalSigns (Queries) ⚠️

**CSV Specification:**
- Method: `Queries PUT ShortQuery`
- Endpoint: `https://api.opendental.com/api/v1/queries/ShortQuery`
- Parameter: `{AptNum}`
- Example Output: DateTaken, Pulse, BP, Height, Weight
- Note: "BMI calculation needed: (Weight/Height^2)*703"

**Current Implementation:**
```python
async def fetch_vital_signs(self, aptnum: int) -> EndpointResponse:
    start_time = time.time()
    try:
        query_body = {
            "query": f"SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum={aptnum}"
        }
        response = await asyncio.wait_for(
            self._make_request("PUT", "/queries/ShortQuery", json=query_body),
            timeout=45.0,
        )
```

**Assessment:** ❓ **NEEDS VERIFICATION**

**Potential Issues:**

1. **Table Name:**
   - Current: `vitalsign`
   - Possible alternatives: `vital_signs`, `VitalSigns`, `VitalSign`
   - Database table names are often case-sensitive

2. **Column Names:**
   - Current: `DateTaken, Pulse, BP, Height, Weight`
   - CSV shows these in example output, but SQL schema might differ
   - May need exact casing: `datetaken` vs `DateTaken`

3. **WHERE Clause Syntax:**
   - Current: `WHERE AptNum={aptnum}` (no spaces)
   - May need: `WHERE AptNum = {aptnum}` (with spaces)
   - Or: `WHERE AptNum={aptnum}` (exact format in CSV not shown)

4. **Query Structure:**
   - Current: Plain SQL SELECT statement
   - May need specific ShortQuery format or wrapper

**Recommendation:** 
1. Check OpenDental ShortQuery API documentation
2. Verify exact table and column names from database schema
3. Test query with sample AptNum value
4. Add error handling for SQL syntax errors (500 responses)

---

## Base URL Analysis

**CSV Shows:**
```
https://api.opendental.com/api/v1/{endpoint}
```

**Current Implementation:**
```python
self.base_url = str(credential.base_url).rstrip("/")
# Then constructs: f"{self.base_url}/procedurelogs?AptNum={aptnum}"
```

**Question:** Does `credential.base_url` include `/api/v1`?

**Test Cases:**
- If base_url = `https://api.opendental.com/api/v1`, then final URL = `https://api.opendental.com/api/v1/procedurelogs?AptNum={aptnum}` ✅
- If base_url = `https://api.opendental.com`, then final URL = `https://api.opendental.com/procedurelogs?AptNum={aptnum}` ❌ (missing `/api/v1`)

**Recommendation:** Verify credential configuration includes `/api/v1` in base URL.

---

## Testing Strategy

### Phase 1: Individual Endpoint Testing

Test each endpoint individually with user's parameters:
- PatNum: 39689
- AptNum: 99413

Expected Results:

| Endpoint | Expected Status | Current Implementation | Priority |
|----------|----------------|----------------------|----------|
| ProcedureLogs | 200 OK | Likely working | High |
| Allergies | 200 OK | Likely working | High |
| MedicationPats | 200 OK | Likely working | High |
| Diseases | 200 OK | Likely working | High |
| PatientNotes | 200 OK or 404 | Test both formats | Critical |
| VitalSigns | 200 OK or 400/500 | Verify SQL syntax | Critical |

### Phase 2: Error Pattern Analysis

Common Error Responses:

**404 Not Found:**
- Indicates wrong URL path
- For PatientNotes: Try switching between path/query parameter

**400 Bad Request:**
- Indicates malformed request
- For VitalSigns: Check SQL syntax, table/column names

**401 Unauthorized:**
- Should be fixed by ODFHIR authorization update
- If still occurring, double-check Authorization header

**500 Internal Server Error:**
- For VitalSigns: Likely SQL syntax error
- Check database table/column names

### Phase 3: Response Validation

For 200 OK responses, verify JSON structure matches CSV examples:

**ProcedureLogs:**
```json
{
  "ProcCode": "D0220",
  "Descript": "...",
  "ProcFee": "31.00",
  "ProcStatus": "TP"
}
```

**VitalSigns:**
```json
{
  "DateTaken": "2025-11-11T00:00:00",
  "Pulse": 122,
  "BP": "123/321",
  "Height": 231.0,
  "Weight": 98.0
}
```

---

## Decisions & Recommendations

### Decision 1: PatientNotes URL Format

**Options:**
- A. Keep path parameter: `/patientnotes/{patnum}` (current)
- B. Switch to query parameter: `/patientnotes?PatNum={patnum}`

**Decision:** Test Option A first (path parameter), as it's RESTful convention for single resource. If 404, try Option B.

**Rationale:** CSV note "PatNum is required to be in the URL" is ambiguous but OpenDental API likely follows REST conventions where retrieving a single resource uses path parameters.

---

### Decision 2: VitalSigns Query Structure

**Current Query:**
```sql
SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum={aptnum}
```

**Recommendations:**
1. Verify table name with OpenDental schema documentation
2. Test with sample AptNum to get actual error message
3. Add logging to capture full SQL error responses
4. Consider parameterized query if API supports it (SQL injection prevention)

**Alternatives to Test:**
```sql
-- Option A: Exact column casing
SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum = 99413

-- Option B: Lowercase
SELECT datetaken, pulse, bp, height, weight FROM vitalsign WHERE aptnum = 99413

-- Option C: Different table name
SELECT DateTaken, Pulse, BP, Height, Weight FROM vital_signs WHERE AptNum = 99413
```

---

### Decision 3: Base URL Configuration

**Action Required:** Verify `credential.base_url` in stored credentials includes `/api/v1` prefix.

**Test:**
```python
# Check credential configuration
credential = get_credentials(password="...")
print(f"Base URL: {credential.base_url}")
# Should print: https://api.opendental.com/api/v1
```

**If missing `/api/v1`:**
- Update credential prompt to clarify base URL should include version
- Or: Modify api_client.py to append `/api/v1` if not present

---

## Actual Test Results (2025-12-02)

### Root Cause Identified ✅

**Problem:** `EndpointResponse.data` field was typed as `dict[str, Any]` but API returns:
- **Arrays/Lists** for collection endpoints (procedurelogs, allergies, medicationpats, diseases)
- **Single Dict** for single resource endpoint (patientnotes)

**Error Message:**
```
Unexpected error: 1 validation error for EndpointResponse\ndata\n
Input should be a valid dictionary [type=dict_type, input_value=[{...}], input_type=list]
```

### Test Results by Endpoint

| Endpoint | Status | Error | Root Cause |
|----------|--------|-------|------------|
| ProcedureLogs | ❌ Failed | Pydantic validation error | Returns **list**, model expected **dict** |
| Allergies | ❌ Failed | Pydantic validation error | Returns **list**, model expected **dict** |
| MedicationPats | ❌ Failed | Pydantic validation error | Returns **list**, model expected **dict** |
| Diseases | ❌ Failed | Pydantic validation error | Returns **list**, model expected **dict** |
| PatientNotes | ✅ **WORKED** | None | Returns **dict** (matches model) |
| VitalSigns | ❌ Failed | Client error (400) | SQL query format issue |

### Fix Applied ✅

**File:** `src/opendental_cli/models/response.py`

**Changed:**
```python
# BEFORE
data: dict[str, Any] | None

# AFTER  
data: dict[str, Any] | list[dict[str, Any]] | None
```

This allows the model to accept both:
- Single resource responses (dict) - e.g., PatientNotes
- Collection responses (list) - e.g., ProcedureLogs, Allergies, etc.

### VitalSigns 400 Error

**Status:** Still investigating

**Possible Causes:**
1. SQL query syntax incorrect for ShortQuery endpoint
2. Table name case sensitivity: `vitalsign` vs `VitalSign`  
3. WHERE clause format: Added space `WHERE AptNum = {aptnum}` (was `WHERE AptNum={aptnum}`)
4. Query body structure may need different format

**Next Steps:**
- Test with updated WHERE clause (space added)
- May need to check OpenDental API documentation for exact query format
- Consider trying different table names if still fails

## Resolved Questions

1. ✅ **Which endpoint worked?** PatientNotes (only endpoint returning dict instead of list)
2. ✅ **Error messages?** Pydantic validation errors - input_type=list but expected dict
3. ✅ **Why others failed?** API returns arrays but model expected single dict
4. ❓ **VitalSigns SQL format?** Still investigating 400 error

---

## Next Steps

1. **Immediate:** Test all 6 endpoints individually with PatNum=39689, AptNum=99413
2. **Document:** Capture HTTP status codes and error messages for each
3. **Fix:** Update PatientNotes and/or VitalSigns based on test results
4. **Validate:** Run full orchestrator with all 6 endpoints
5. **Test:** Update integration tests with correct formats
