# Research: OpenDental FHIR Authorization Format Issue

**Date**: 2025-12-02  
**Phase**: 0 - Research  
**Status**: Complete

## Executive Summary

**Issue**: CLI experiencing 401 Unauthorized on all OpenDental API endpoints despite valid credentials.

**Root Cause**: Incorrect authorization header format. Current implementation sends separate `DeveloperKey` and `CustomerKey` headers, but OpenDental FHIR API requires single `Authorization: ODFHIR {key1}/{key2}` header.

**Solution**: Modify `get_auth_header()` in `credential.py` to combine keys into ODFHIR format.

---

## Investigation Process

### Step 1: Error Analysis

**User Report**:
- Command: `opendental-cli --patnum 39689 --aptnum 99413`
- Result: Exit code 1 (failure)
- Error: 401 Unauthorized on ALL endpoints

**Significance**: 
- Not a credentials issue (all endpoints fail, not just some)
- Not an endpoint-specific issue (affects all 6 endpoints)
- Likely an authentication format problem

### Step 2: Current Implementation Review

**File**: `src/opendental_cli/models/credential.py`

```python
def get_auth_header(self) -> dict[str, str]:
    """Generate Authorization headers.
    
    SecretStr ensures keys not leaked in logs.
    Both developer_key and customer_key are required for API authentication.
    
    Returns:
        Authorization headers dict with both keys
    """
    return {
        "DeveloperKey": self.developer_key.get_secret_value(),
        "CustomerKey": self.customer_key.get_secret_value(),
    }
```

**Observation**: Code sends two separate custom headers (`DeveloperKey`, `CustomerKey`).

**File**: `src/opendental_cli/api_client.py` (Line 58)

```python
self.client = httpx.AsyncClient(
    base_url=credential.base_url,
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        **credential.get_auth_header(),  # Spreads DeveloperKey and CustomerKey
    },
    timeout=httpx.Timeout(10.0, read=30.0, write=10.0, pool=5.0),
    verify=True,
)
```

**Observation**: Client correctly spreads auth headers into HTTPX client. The spreading mechanism works fine; the problem is what's being spread.

### Step 3: API Documentation Review

**File**: `specs/001-audit-data-cli/contracts/opendental-api.md`

```markdown
**Authentication**: Custom Headers  
**Headers**: 
- `DeveloperKey: {developer_key}`
- `CustomerKey: {customer_key}`
```

**Observation**: Internal documentation was wrong! It specified custom headers, but this doesn't match actual OpenDental FHIR API requirements.

### Step 4: User Clarification

**User Statement**: "Authorization should be in the form of ODFHIR {DeveloperKey}/{DeveloperPortalKey}."

**Critical Discovery**: 
- Not separate headers - single `Authorization` header
- Format: `ODFHIR {key1}/{key2}`
- ODFHIR is the authentication scheme prefix
- Keys are separated by forward slash `/`

### Step 5: OpenDental FHIR API Format

**Correct Format**:
```http
GET /api/v1/allergies?PatNum=12345 HTTP/1.1
Host: example.opendental.com
Authorization: ODFHIR dev_key_abc123/portal_key_xyz789
Accept: application/json
```

**Not**:
```http
GET /api/v1/allergies?PatNum=12345 HTTP/1.1
Host: example.opendental.com
DeveloperKey: dev_key_abc123
CustomerKey: portal_key_xyz789
Accept: application/json
```

---

## Root Cause Analysis

### Why 401 Errors Occur

1. **Missing Authorization Header**: API expects `Authorization` header, receives none
2. **Unrecognized Headers**: `DeveloperKey` and `CustomerKey` are not standard HTTP headers and are ignored by the API
3. **Authentication Failure**: Without proper `Authorization` header, API treats request as unauthenticated
4. **Result**: 401 Unauthorized response

### Why Previous Implementation Was Wrong

**Hypothesis**: Original contract documentation was written based on assumptions or incomplete API research rather than actual API testing. The two-key authentication system was correctly identified, but the header format was incorrectly documented as separate custom headers instead of the combined ODFHIR format.

**Evidence**:
- No tests verify actual HTTP headers sent (only that credentials are passed to client)
- Contract documentation doesn't reference OpenDental FHIR specification
- User's manual testing revealed the discrepancy

---

## Solution Design

### Approach 1: Modify Header Construction (SELECTED)

**Change**: Update `get_auth_header()` to return single Authorization header

**Pros**:
- Minimal code change (one method)
- Credential storage logic unchanged
- Existing tests can be updated easily
- No breaking changes to credential management

**Cons**:
- Need to update all tests that verify headers
- Need to update API contract documentation

**Implementation**:
```python
def get_auth_header(self) -> dict[str, str]:
    """Generate OpenDental FHIR Authorization header.
    
    OpenDental FHIR API uses format: Authorization: ODFHIR {key1}/{key2}
    where key1 is Developer Key and key2 is Developer Portal Key.
    
    Returns:
        Authorization header dict with ODFHIR format
    """
    developer_key = self.developer_key.get_secret_value()
    portal_key = self.customer_key.get_secret_value()
    return {
        "Authorization": f"ODFHIR {developer_key}/{portal_key}"
    }
```

### Approach 2: Create Separate Method (REJECTED)

**Change**: Keep `get_auth_header()`, add `get_odfhir_auth()`

**Pros**:
- Preserves backward compatibility (though nothing else uses old format)

**Cons**:
- Adds unnecessary complexity
- Confusing to have two auth methods
- No actual backward compatibility need (API never worked with old format)

**Decision**: Rejected - no benefit to keeping broken implementation

---

## Field Naming Clarification

### Current Field Names

```python
developer_key: SecretStr  # First part of ODFHIR auth
customer_key: SecretStr   # Second part of ODFHIR auth
```

### More Accurate Names

```python
developer_key: SecretStr         # Developer Key (from OpenDental Developer Portal)
developer_portal_key: SecretStr  # Developer Portal Key (customer-specific)
```

### Decision: Keep Existing Names

**Rationale**:
- Changing field names requires credential migration
- Existing credentials stored in keyring would become inaccessible
- Field names are internal - users only see prompts
- Can clarify with better prompts and documentation

**Action**: Update CLI prompts to say "Developer Portal Key" instead of "Customer Key" for clarity, but keep `customer_key` field name internally.

---

## Testing Strategy

### Unit Tests

**Test**: `test_credential_get_auth_header_odfhir_format()`

```python
def test_credential_get_auth_header_odfhir_format():
    """Test get_auth_header returns ODFHIR format."""
    credential = APICredential(
        base_url="https://example.com/api/v1",
        developer_key="test_dev_key",
        customer_key="test_portal_key",
    )
    
    auth_header = credential.get_auth_header()
    
    # Verify single Authorization header
    assert len(auth_header) == 1
    assert "Authorization" in auth_header
    
    # Verify ODFHIR format
    auth_value = auth_header["Authorization"]
    assert auth_value.startswith("ODFHIR ")
    assert "/" in auth_value
    assert "test_dev_key" in auth_value
    assert "test_portal_key" in auth_value
    
    # Verify old headers not present
    assert "DeveloperKey" not in auth_header
    assert "CustomerKey" not in auth_header
```

### Contract Tests

Update all contract tests to verify Authorization header:

```python
@respx.mock
async def test_fetch_allergies_uses_odfhir_auth(api_client):
    """Verify allergies endpoint uses ODFHIR authorization."""
    respx.get("https://example.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(200, json={"PatNum": 12345, "allergies": []})
    )
    
    await api_client.fetch_allergies(12345)
    
    # Verify Authorization header sent
    request = respx.calls.last.request
    assert "Authorization" in request.headers
    assert request.headers["Authorization"].startswith("ODFHIR ")
    assert "/" in request.headers["Authorization"]
```

### Integration Tests

Update mocked API to accept Authorization header:

```python
@respx.mock
def test_golden_path_with_odfhir_auth():
    """Test CLI with ODFHIR authorization format."""
    # Mock API accepts Authorization header
    respx.route(
        headers__contains={"Authorization": "ODFHIR"}
    ).mock(return_value=httpx.Response(200, json={}))
    
    # Run CLI command
    result = runner.invoke(main, ["--patnum", "12345", "--aptnum", "67890"])
    
    assert result.exit_code == 0
```

---

## Risk Assessment

### Low Risk Changes

✅ **Credential Storage**: No changes to keyring integration  
✅ **Credential Retrieval**: No changes to `get_credentials()`  
✅ **CLI Arguments**: No changes to command-line interface  
✅ **Error Handling**: No changes to retry logic or error categorization  

### Medium Risk Changes

⚠️ **Header Construction**: Single method change in `get_auth_header()`
- **Risk**: Typo in format string could cause continued 401 errors
- **Mitigation**: Unit test verifies exact format before deployment

⚠️ **Test Updates**: Need to update ~15 test files
- **Risk**: Missing a test could cause false passes
- **Mitigation**: Run full test suite, verify coverage doesn't decrease

### High Risk Areas (None Identified)

No high-risk changes. This is a focused fix with clear scope.

---

## Dependencies & Constraints

### No New Dependencies

- Uses existing `pydantic` for model
- Uses existing `httpx` for HTTP client
- No new packages required

### No Breaking Changes

- Credential storage format unchanged
- CLI command interface unchanged
- Output format unchanged
- Only change is internal header construction

### HIPAA Compliance Maintained

- Authorization header uses `SecretStr` (not logged)
- No PHI in header (only authentication credentials)
- Existing sanitization logic unchanged
- Keyring encryption unchanged

---

## Implementation Checklist

### Code Changes

- [ ] Update `get_auth_header()` in credential.py
- [ ] Update CLI prompt in cli.py (Customer Key → Developer Portal Key)
- [ ] Verify api_client.py spreads header correctly (already does)

### Test Changes

- [ ] Add unit test: test_credential_get_auth_header_odfhir_format
- [ ] Update contract tests: verify Authorization header
- [ ] Update integration tests: mock Authorization header
- [ ] Run full test suite: pytest --cov

### Documentation Changes

- [ ] Update opendental-api.md: correct authentication section
- [ ] Update README.md: add authentication section
- [ ] Update SECURITY.md: document ODFHIR format

### Verification

- [ ] Unit tests pass
- [ ] Contract tests pass
- [ ] Integration tests pass
- [ ] Coverage remains ≥90%
- [ ] Manual test with real credentials returns 200 OK

---

## Timeline Estimate

| Phase | Task | Time |
|-------|------|------|
| 0 | Research | ✅ Complete (30 min) |
| 1 | Code changes | 10 min |
| 1 | Test updates | 20 min |
| 1 | Documentation | 15 min |
| 2 | Test execution | 5 min |
| 2 | Manual verification | 15 min |
| **Total** | | **1 hour 35 min** |

---

## Success Criteria

1. ✅ Root cause identified and documented
2. ✅ Solution approach selected with justification
3. ✅ Testing strategy defined
4. ✅ Risk assessment complete
5. ✅ Implementation plan ready

**Status**: Ready for Phase 1 (Implementation)

---

## References

- User clarification: "Authorization should be in the form of ODFHIR {DeveloperKey}/{DeveloperPortalKey}"
- Current implementation: `src/opendental_cli/models/credential.py`
- API contract: `specs/001-audit-data-cli/contracts/opendental-api.md`
- Constitution: `.specify/memory/constitution.md` (Articles II, IV)
