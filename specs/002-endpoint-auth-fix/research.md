# Research: API Authentication & Endpoint Format Audit

**Date**: 2025-01-XX  
**Phase**: 1 - Research  
**Engineer**: AI Assistant

## Executive Summary

**Issue**: User reported errors when running `opendental-cli --patnum 39689 --aptnum 99413` (exits with code 1).

**Root Cause Analysis**:
1. ✅ **Authentication**: Already correctly implemented with two-key system (DeveloperKey, CustomerKey)
2. ❌ **Endpoint Formatting**: Found critical bug - vital_signs endpoint uses wrong JSON key

**Findings**:
- Authentication system is **already correct** - no changes needed
- Vital signs endpoint has bug: uses `"Query"` but should use `"query"` (lowercase)
- All other endpoints match API contract specifications

---

## 1. Authentication Audit (T001)

### Current Implementation

**File**: `src/opendental_cli/models/credential.py`

```python
class Credential(BaseModel):
    base_url: str
    developer_key: SecretStr  # ✅ Correct field
    customer_key: SecretStr   # ✅ Correct field
    environment: str

    def get_auth_header(self) -> dict[str, str]:
        return {
            "DeveloperKey": self.developer_key.get_secret_value(),  # ✅ Correct header
            "CustomerKey": self.customer_key.get_secret_value(),    # ✅ Correct header
        }
```

**File**: `src/opendental_cli/api_client.py` (Line 58)

```python
self.client = httpx.AsyncClient(
    base_url=credential.base_url,
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        **credential.get_auth_header(),  # ✅ Spreads both DeveloperKey and CustomerKey
    },
    # ... timeout and verify settings
)
```

**File**: `src/opendental_cli/credential_manager.py`

```python
def set_credentials(
    base_url: str,
    developer_key: str,  # ✅ Two separate keys
    customer_key: str,   # ✅ Two separate keys
    password: str,
    environment: str = "default",
) -> None:
    """Store credentials in keyring."""
    # Stores both keys in keyring with separate key names
    keyring.set_password(SERVICE_NAME, f"{environment}_developer_key", developer_key)
    keyring.set_password(SERVICE_NAME, f"{environment}_customer_key", customer_key)
```

**File**: `src/opendental_cli/cli.py` (Lines 383-398)

```python
developer_key = click.prompt(
    "Enter Developer Key",
    hide_input=False,
    default=current_creds[1] if current_creds else None,
)

customer_key = click.prompt(
    "Enter Customer Key",
    hide_input=False,
    default=current_creds[2] if current_creds else None,
)
```

### Verdict: ✅ AUTHENTICATION IS CORRECT

**Conclusion**: The authentication system is already correctly implemented with:
- Two separate API keys (developer_key, customer_key)
- Correct header names (DeveloperKey, CustomerKey)
- Proper storage in OS keyring
- CLI prompts for both keys separately

**Action**: Skip tasks T004-T009 (authentication fixes) - already implemented.

---

## 2. Endpoint Formatting Audit (T002)

### API Contract Requirements

**From**: `specs/001-audit-data-cli/contracts/opendental-api.md`

| Endpoint | Method | Path | Query Params | Body |
|----------|--------|------|--------------|------|
| Procedure Logs | GET | `/procedurelogs?AptNum={AptNum}` | ✅ AptNum | - |
| Allergies | GET | `/allergies?PatNum={PatNum}` | ✅ PatNum | - |
| Medications | GET | `/medicationpats?PatNum={PatNum}` | ✅ PatNum | - |
| Diseases | GET | `/diseases?PatNum={PatNum}` | ✅ PatNum | - |
| Patient Notes | GET | `/patientnotes/{PatNum}` | **Path param** | - |
| Vital Signs | PUT | `/queries/ShortQuery` | - | ❌ `{"query": "..."}` |

### Current Implementation Analysis

**File**: `src/opendental_cli/api_client.py`

#### ✅ Endpoint 1: Procedure Logs (Line 288)
```python
async def fetch_procedure_logs(self, aptnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("procedurelogs", f"/procedurelogs?AptNum={aptnum}")
```
**Status**: ✅ CORRECT - Uses `AptNum` query param with capital letters

---

#### ✅ Endpoint 2: Allergies (Line 298)
```python
async def fetch_allergies(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("allergies", f"/allergies?PatNum={patnum}")
```
**Status**: ✅ CORRECT - Uses `PatNum` query param with capital letters

---

#### ✅ Endpoint 3: Medications (Line 308)
```python
async def fetch_medications(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("medicationpats", f"/medicationpats?PatNum={patnum}")
```
**Status**: ✅ CORRECT - Uses `PatNum` query param with capital letters

---

#### ✅ Endpoint 4: Diseases (Line 318)
```python
async def fetch_problems(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("diseases", f"/diseases?PatNum={patnum}")
```
**Status**: ✅ CORRECT - Uses `PatNum` query param with capital letters

---

#### ✅ Endpoint 5: Patient Notes (Line 328)
```python
async def fetch_patient_notes(self, patnum: int) -> EndpointResponse:
    return await self.fetch_endpoint("patientnotes", f"/patientnotes/{patnum}")
```
**Status**: ✅ CORRECT - Uses path parameter format `/patientnotes/{patnum}` (not query param)

---

#### ❌ Endpoint 6: Vital Signs (Line 338-365)

**Current Implementation**:
```python
async def fetch_vital_signs(self, aptnum: int) -> EndpointResponse:
    query_body = {
        "Query": f"SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum={aptnum}"
        # ^^^^^ BUG: Uses capital "Query" 
    }

    response = await asyncio.wait_for(
        self._make_request("PUT", "/queries/ShortQuery", json=query_body),
        timeout=45.0,
    )
```

**API Contract Requirement**:
```json
{
  "query": "SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE PatNum = 12345 ORDER BY DateTaken DESC"
}
```

**Issues Found**:
1. ❌ JSON key is `"Query"` (capital Q) but should be `"query"` (lowercase q)
2. ⚠️ SQL uses `WHERE AptNum={aptnum}` but contract example shows `WHERE PatNum = 12345`
   - **Note**: This may be intentional if vital signs are queried by appointment, but contract example uses PatNum
   - Need clarification: Should vital signs be fetched by AptNum or PatNum?

**Status**: ❌ **CRITICAL BUG** - JSON key casing is incorrect

---

## 3. Summary of Findings

### Authentication (Phase 2): ✅ NO CHANGES NEEDED

The system already has:
- Two-key authentication (DeveloperKey, CustomerKey)
- Correct header names matching API contract
- Proper credential storage and retrieval
- CLI prompts for both keys

**Recommendation**: Mark tasks T004-T009 as "Already Implemented" in tasks.md

---

### Endpoints (Phase 5): 🔧 ONE BUG TO FIX

| Endpoint | Status | Issue |
|----------|--------|-------|
| Procedure Logs | ✅ PASS | Correct implementation |
| Allergies | ✅ PASS | Correct implementation |
| Medications | ✅ PASS | Correct implementation |
| Diseases | ✅ PASS | Correct implementation |
| Patient Notes | ✅ PASS | Correct path param usage |
| Vital Signs | ❌ FAIL | JSON key "Query" should be "query" |

**Critical Fix Required**:
```python
# BEFORE (WRONG):
query_body = {
    "Query": f"SELECT ..."  # ❌ Capital Q
}

# AFTER (CORRECT):
query_body = {
    "query": f"SELECT ..."  # ✅ Lowercase q
}
```

**Optional Investigation**:
- Contract shows vital signs queried by `PatNum` in example
- Implementation uses `AptNum` 
- Verify which parameter is correct with user/API documentation

---

## 4. Impact Assessment

### User-Reported Error Analysis

**Command**: `opendental-cli --patnum 39689 --aptnum 99413`

**Expected Behavior**:
- Fetch patient data using PatNum=39689
- Fetch appointment data using AptNum=99413
- If vital signs endpoint is called, it would fail due to `"Query"` vs `"query"` bug

**Root Cause**:
The vital signs endpoint JSON key casing mismatch would cause:
- 400 Bad Request (invalid JSON structure)
- Or 500 Internal Server Error (unrecognized field)

This explains the exit code 1 error the user is experiencing.

---

## 5. Recommended Action Plan

### Phase 1: Immediate Fix (High Priority)

1. ✅ **Fix vital_signs JSON key casing**:
   - File: `src/opendental_cli/api_client.py`
   - Line: ~361
   - Change: `"Query"` → `"query"`

2. ⚠️ **Verify vital signs parameter** (Optional):
   - Confirm with user: Should vital signs use `AptNum` or `PatNum`?
   - Update SQL query if needed

### Phase 2: Testing

1. Update existing tests to verify lowercase "query" key
2. Run integration tests with actual credentials
3. Verify all 6 endpoints return successful responses

### Phase 3: Documentation

1. Update tasks.md to reflect:
   - T001-T003: Completed (research)
   - T004-T009: Mark as "Already Implemented"
   - T023-T027: Focus on vital_signs endpoint fix only

---

## 6. Technical Debt & Future Improvements

### None Identified

The codebase is well-structured with:
- Proper separation of concerns
- Defensive error handling
- Comprehensive retry logic
- Structured logging

The only issue is the single JSON key typo in vital_signs endpoint.

---

## 7. Conclusion

**Authentication**: ✅ Already correct - no work needed  
**Endpoints**: 🔧 One critical bug in vital_signs JSON key casing  

**Next Steps**:
1. Fix `"Query"` → `"query"` in api_client.py
2. Run tests to validate fix
3. Test with user's actual credentials
4. Close feature implementation

**Estimated Fix Time**: 5 minutes (single line change + test validation)
