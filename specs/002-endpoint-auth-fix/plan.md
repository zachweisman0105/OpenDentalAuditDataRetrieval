# Implementation Plan: OpenDental API Endpoint Authorization & Format Fix

**Feature**: 002-endpoint-auth-fix  
**Created**: 2025-12-02  
**Branch**: `feature/002-endpoint-auth-fix`

## Phase 0: Research & Discovery

### Task R001: Audit Current Authentication Implementation
**Owner**: Developer  
**Estimated Time**: 30 minutes  
**Description**: Review how authentication headers are currently constructed and sent

**Steps**:
1. Read `src/opendental_cli/models/credential.py` - check APICredential fields
2. Read `APICredential.get_auth_header()` method - verify header construction
3. Read `src/opendental_cli/api_client.py` - check how headers are set in HTTPX client
4. Compare against `specs/001-audit-data-cli/contracts/opendental-api.md` authentication specification
5. Document discrepancies: field names, header names, header values

**Expected Output**: Written analysis of authentication implementation vs contract spec

**Deliverables**:
- `specs/002-endpoint-auth-fix/research.md` with authentication audit section

---

### Task R002: Audit Current Endpoint URL Construction
**Owner**: Developer  
**Estimated Time**: 30 minutes  
**Description**: Review how endpoint URLs are constructed in each fetch_* method

**Steps**:
1. List all 6 fetch methods in api_client.py: procedure_logs, allergies, medications, problems, patient_notes, vital_signs
2. For each method, document:
   - HTTP method used (GET, POST, PUT)
   - Path format (query params vs path params)
   - Parameter names and casing
3. Compare against contract spec for each endpoint
4. Flag mismatches: wrong method, wrong path format, wrong parameter names

**Expected Output**: Comparison table of implemented vs contract-specified formats

**Deliverables**:
- `specs/002-endpoint-auth-fix/research.md` with endpoint format audit section

---

### Task R003: Test Against Live API (if credentials available)
**Owner**: Developer  
**Estimated Time**: 20 minutes  
**Description**: Attempt to call live API with current implementation to capture actual error responses

**Steps**:
1. Configure test credentials in keyring
2. Run `opendental-cli --patnum 12345 --aptnum 67890` (with actual test IDs if available)
3. Capture error output and HTTP status codes
4. Review audit.log for error details
5. Identify if errors are 401/403 (auth) or 400/404 (format)

**Expected Output**: Error log analysis showing authentication vs format errors

**Deliverables**:
- `specs/002-endpoint-auth-fix/research.md` with live API test results section

---

## Phase 1: Fix Authentication (Critical Path)

### Task F001: Update APICredential Model
**Owner**: Developer  
**Estimated Time**: 15 minutes  
**Files**: `src/opendental_cli/models/credential.py`

**Changes Required**:
```python
# CURRENT (suspected):
class APICredential(BaseModel):
    base_url: HttpUrl
    api_key: SecretStr
    environment: str

# SHOULD BE:
class APICredential(BaseModel):
    base_url: HttpUrl
    developer_key: SecretStr  # Changed from api_key
    customer_key: SecretStr   # Added second key
    environment: str
```

**Steps**:
1. Update field names: `api_key` → `developer_key`, add `customer_key`
2. Update `get_auth_header()` method to return dict with both headers
3. Update docstrings to reflect two separate keys

**Testing**:
- Unit test: Verify model validates with both keys
- Unit test: Verify get_auth_header() returns correct dict structure

**Deliverables**:
- Updated `credential.py` with two-key model
- Updated unit tests in `tests/unit/test_models.py`

---

### Task F002: Update Credential Manager Storage
**Owner**: Developer  
**Estimated Time**: 20 minutes  
**Files**: `src/opendental_cli/credential_manager.py`

**Changes Required**:
1. Update `set_credentials()` to accept `developer_key` and `customer_key` parameters
2. Update keyring storage to store both keys separately:
   - `{environment}_developer_key`
   - `{environment}_customer_key`
3. Update `_get_from_keyring()` to retrieve both keys
4. Update `_get_from_env()` to check `OPENDENTAL_DEVELOPER_KEY` and `OPENDENTAL_CUSTOMER_KEY`

**Steps**:
1. Modify function signatures
2. Update keyring.set_password() calls (2 keys instead of 1)
3. Update keyring.get_password() calls (2 keys instead of 1)
4. Update environment variable names in fallback logic

**Testing**:
- Unit test: Verify both keys stored in keyring
- Unit test: Verify both keys retrieved from keyring
- Unit test: Verify both keys retrieved from env vars

**Deliverables**:
- Updated `credential_manager.py` with two-key storage
- Updated unit tests in `tests/unit/test_credential_manager.py`

---

### Task F003: Update CLI Credential Prompts
**Owner**: Developer  
**Estimated Time**: 15 minutes  
**Files**: `src/opendental_cli/cli.py`

**Changes Required**:
1. Update `config set-credentials` command to prompt for two keys separately:
   - "Enter Developer Key"
   - "Enter Customer Key"
2. Update validation to ensure both keys are non-empty
3. Pass both keys to set_credentials()

**Steps**:
1. Modify prompt sequence in set_credentials_cmd()
2. Add validation for both keys
3. Update call to credential_manager.set_credentials()

**Testing**:
- Integration test: Verify prompts work correctly
- Integration test: Verify both keys stored after config command

**Deliverables**:
- Updated `cli.py` with two-key prompts
- Updated integration tests in `tests/integration/test_credential_flow.py`

---

### Task F004: Verify Authentication Headers in API Client
**Owner**: Developer  
**Estimated Time**: 10 minutes  
**Files**: `src/opendental_cli/api_client.py`

**Changes Required**:
1. Verify `get_auth_header()` returns:
   ```python
   {
       "DeveloperKey": self.developer_key.get_secret_value(),
       "CustomerKey": self.customer_key.get_secret_value()
   }
   ```
2. Verify headers dict is spread into HTTPX client headers
3. Confirm no other auth methods (Bearer token, etc.) are being used

**Steps**:
1. Review OpenDentalAPIClient.__init__() headers construction
2. Verify credential.get_auth_header() is called and unpacked
3. Add logging to confirm headers are set correctly

**Testing**:
- Unit test: Mock HTTPX client, verify headers passed correctly
- Integration test: Capture actual HTTP request, verify headers present

**Deliverables**:
- Verified or updated `api_client.py` with correct header handling
- Test that verifies header format

---

## Phase 2: Fix Endpoint Formats

### Task E001: Fix patient_notes Endpoint (Path Parameter)
**Owner**: Developer  
**Estimated Time**: 10 minutes  
**Files**: `src/opendental_cli/api_client.py`

**Issue**: Contract specifies `GET /patientnotes/{PatNum}` (path parameter), not query parameter

**Current** (suspected):
```python
return await self.fetch_endpoint("patientnotes", f"/patientnotes?PatNum={patnum}")
```

**Should Be**:
```python
return await self.fetch_endpoint("patientnotes", f"/patientnotes/{patnum}")
```

**Steps**:
1. Update fetch_patient_notes() method
2. Change URL from query param to path param

**Testing**:
- Contract test: Mock 200 response for /patientnotes/12345
- Verify fetch_patient_notes(12345) calls correct URL

**Deliverables**:
- Updated fetch_patient_notes() in api_client.py
- Updated contract test

---

### Task E002: Fix vital_signs Query Body (Capital Q)
**Owner**: Developer  
**Estimated Time**: 10 minutes  
**Files**: `src/opendental_cli/api_client.py`

**Issue**: Contract specifies JSON body with key "Query" (capital Q), verify implementation matches

**Current** (line 360 in api_client.py):
```python
query_body = {
    "Query": f"SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum={aptnum}"
}
```

**Action**: Verify this is correct (capital Q). If using lowercase "query", change to capital "Query"

**Steps**:
1. Review fetch_vital_signs() method
2. Verify query_body uses "Query" key
3. Verify SQL query uses correct table name and column names per contract

**Testing**:
- Contract test: Verify PUT request body has "Query" key
- Verify SQL query matches contract spec

**Deliverables**:
- Verified or updated fetch_vital_signs() in api_client.py
- Updated contract test if needed

---

### Task E003: Verify Query Parameter Casing
**Owner**: Developer  
**Estimated Time**: 15 minutes  
**Files**: `src/opendental_cli/api_client.py`

**Issue**: Ensure query parameter names match contract exactly (case-sensitive)

**Contract Specifications**:
- `procedurelogs?AptNum={AptNum}` (capital A, capital N)
- `allergies?PatNum={PatNum}` (capital P, capital N)
- `medicationpats?PatNum={PatNum}` (capital P, capital N)
- `diseases?PatNum={PatNum}` (capital P, capital N)

**Steps**:
1. Review all fetch_* methods
2. Verify parameter casing matches contract
3. Update if mismatches found (e.g., "patnum" vs "PatNum")

**Testing**:
- Contract tests: Verify request URLs match expected format
- Integration test: Verify all endpoints return 200 with correct params

**Deliverables**:
- Verified or updated all fetch_* methods
- Updated contract tests if needed

---

## Phase 3: Documentation & Testing

### Task D001: Update API Contract Documentation
**Owner**: Developer  
**Estimated Time**: 20 minutes  
**Files**: `specs/001-audit-data-cli/contracts/opendental-api.md`

**Changes Required**:
1. Verify all endpoint specifications are accurate
2. Add examples of working requests with correct headers
3. Document any discrepancies found during research
4. Add troubleshooting section for common authentication errors

**Steps**:
1. Review each endpoint specification
2. Add curl examples with DeveloperKey and CustomerKey headers
3. Document tested endpoint behaviors
4. Add error response examples from live testing

**Deliverables**:
- Updated contracts/opendental-api.md with verified specifications

---

### Task D002: Update README with Two-Key Credentials
**Owner**: Developer  
**Estimated Time**: 15 minutes  
**Files**: `README.md`

**Changes Required**:
1. Update credential configuration section to mention both keys
2. Update environment variable examples to show both keys
3. Add troubleshooting section for authentication errors

**Steps**:
1. Update "Configure Credentials" section
2. Show both OPENDENTAL_DEVELOPER_KEY and OPENDENTAL_CUSTOMER_KEY
3. Add "Common Issues" section with 401/403 troubleshooting

**Deliverables**:
- Updated README.md with two-key credential instructions

---

### Task T001: Update All Contract Test Fixtures
**Owner**: Developer  
**Estimated Time**: 30 minutes  
**Files**: `tests/fixtures/*.json`, `tests/contract/*.py`

**Changes Required**:
1. Verify all test fixtures match actual API response format
2. Update mocked responses to include correct structure
3. Update contract tests to verify correct request format

**Steps**:
1. Review all fixture files in tests/fixtures/
2. Compare against contract specifications
3. Update fixture content if mismatches found
4. Update respx mocks to match corrected URLs and methods

**Deliverables**:
- Updated test fixtures
- Updated contract tests with correct expectations

---

### Task T002: Update Integration Tests
**Owner**: Developer  
**Estimated Time**: 20 minutes  
**Files**: `tests/integration/*.py`

**Changes Required**:
1. Update credential flow tests to handle two keys
2. Update mock credentials to include both developer_key and customer_key
3. Verify all integration tests pass with corrected implementation

**Steps**:
1. Review integration test setup
2. Update credential mocking to provide both keys
3. Run integration test suite
4. Fix any failing tests

**Deliverables**:
- Updated integration tests
- All integration tests passing

---

## Phase 4: Validation & Deployment

### Task V001: Manual End-to-End Test
**Owner**: Developer  
**Estimated Time**: 15 minutes  
**Prerequisites**: All previous tasks complete

**Steps**:
1. Reset credentials: `opendental-cli config reset-password`
2. Set new password: `opendental-cli config set-password`
3. Configure credentials with both keys: `opendental-cli config set-credentials`
4. Run full audit retrieval: `opendental-cli --patnum 12345 --aptnum 67890`
5. Verify all 6 endpoints return 200 OK
6. Verify consolidated JSON output contains data from all endpoints

**Success Criteria**:
- Exit code 0
- All 6 endpoints in success section
- No entries in failures section
- Valid JSON output

**Deliverables**:
- Manual test report in research.md

---

### Task V002: Run Full Test Suite
**Owner**: Developer  
**Estimated Time**: 10 minutes  
**Prerequisites**: All previous tasks complete

**Steps**:
1. Run unit tests: `pytest tests/unit/ -v`
2. Run contract tests: `pytest tests/contract/ -v`
3. Run integration tests: `pytest tests/integration/ -v`
4. Verify all tests pass
5. Check coverage: `pytest --cov=opendental_cli --cov-report=term`

**Success Criteria**:
- 0 test failures
- 90%+ coverage maintained

**Deliverables**:
- Test suite results

---

## Summary

**Total Estimated Time**: 4.5 hours

**Critical Path**:
1. Research (R001, R002, R003) - 1.5 hours
2. Authentication fixes (F001-F004) - 1 hour
3. Endpoint fixes (E001-E003) - 35 minutes
4. Testing & validation (T001, T002, V001, V002) - 1 hour 15 minutes
5. Documentation (D001, D002) - 35 minutes

**Risk Areas**:
- May need to migrate existing stored credentials to new two-key format
- Breaking change to credential storage may affect existing users
- Live API testing requires valid test credentials

**Success Metrics**:
- All 6 endpoints return 200 OK
- Authentication errors (401/403) eliminated
- Format errors (400/404) eliminated
- 100% of tests passing
