# Quick Start: Fix ODFHIR Authorization

**Goal**: Fix 401 Unauthorized errors by implementing correct ODFHIR authorization format

**Time**: ~30 minutes implementation + 30 minutes testing

---

## Prerequisites

- [X] Research complete (`research.md`)
- [X] Data model defined (`data-model.md`)
- [X] Python 3.11+ environment
- [X] pytest and dependencies installed

---

## Implementation Steps

### Step 1: Fix Authorization Header (5 min)

**File**: `src/opendental_cli/models/credential.py`

**Find**:
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

**Replace with**:
```python
def get_auth_header(self) -> dict[str, str]:
    """Generate OpenDental FHIR Authorization header.
    
    OpenDental FHIR API uses the ODFHIR authentication scheme:
        Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}
    
    Both keys are required for API authentication. SecretStr ensures
    credentials are not leaked in logs or error messages.
    
    Returns:
        Single-entry dict with Authorization header in ODFHIR format
    """
    developer_key = self.developer_key.get_secret_value()
    portal_key = self.customer_key.get_secret_value()
    
    return {
        "Authorization": f"ODFHIR {developer_key}/{portal_key}"
    }
```

**Verify**: Save file and check no syntax errors

---

### Step 2: Update CLI Prompts (3 min)

**File**: `src/opendental_cli/cli.py`

**Find** (around line 383-390):
```python
customer_key = click.prompt(
    "Enter Customer Key",
    hide_input=False,
    default=current_creds[2] if current_creds else None,
)
```

**Replace with**:
```python
customer_key = click.prompt(
    "Enter Developer Portal Key",
    hide_input=False,
    default=current_creds[2] if current_creds else None,
)
```

**Purpose**: Clarify what "customer key" actually represents in ODFHIR context

---

### Step 3: Add Unit Test (5 min)

**File**: `tests/unit/test_models.py`

**Add at end of file**:
```python
def test_credential_get_auth_header_odfhir_format():
    """Test get_auth_header returns ODFHIR authorization format.
    
    OpenDental FHIR API requires: Authorization: ODFHIR key1/key2
    """
    credential = APICredential(
        base_url="https://example.opendental.com/api/v1",
        developer_key="test_developer_key_abc123",
        customer_key="test_portal_key_xyz789",
    )
    
    auth_header = credential.get_auth_header()
    
    # Verify single Authorization header
    assert len(auth_header) == 1
    assert "Authorization" in auth_header
    
    # Verify ODFHIR format
    auth_value = auth_header["Authorization"]
    assert auth_value == "ODFHIR test_developer_key_abc123/test_portal_key_xyz789"
    
    # Verify old custom headers not present
    assert "DeveloperKey" not in auth_header
    assert "CustomerKey" not in auth_header


def test_credential_get_auth_header_uses_secret_values():
    """Test get_auth_header extracts actual values from SecretStr."""
    credential = APICredential(
        base_url="https://example.opendental.com/api/v1",
        developer_key="secret_dev_key",
        customer_key="secret_portal_key",
    )
    
    auth_header = credential.get_auth_header()
    
    # Verify SecretStr is resolved to actual string
    assert "SecretStr" not in auth_header["Authorization"]
    assert "secret_dev_key" in auth_header["Authorization"]
    assert "secret_portal_key" in auth_header["Authorization"]
```

**Run**:
```bash
pytest tests/unit/test_models.py::test_credential_get_auth_header_odfhir_format -v
pytest tests/unit/test_models.py::test_credential_get_auth_header_uses_secret_values -v
```

**Expected**: Both tests PASS

---

### Step 4: Update Contract Tests (10 min)

**Files**: All files in `tests/contract/`

**Pattern to find**:
```python
# In contract tests that verify headers
assert "DeveloperKey" in request.headers
assert "CustomerKey" in request.headers
```

**Replace with**:
```python
# Verify Authorization header
assert "Authorization" in request.headers
assert request.headers["Authorization"].startswith("ODFHIR ")
assert "/" in request.headers["Authorization"]
```

**Example** - `tests/contract/test_api_client_golden_path.py`:

Add after each API call test:
```python
# Verify ODFHIR authorization header sent
request = respx.calls.last.request
assert "Authorization" in request.headers
assert request.headers["Authorization"].startswith("ODFHIR ")
```

**Run**:
```bash
pytest tests/contract/ -v
```

**Expected**: All contract tests PASS

---

### Step 5: Update Integration Tests (10 min)

**Files**: `tests/integration/test_*.py`

**Update mock routes** to accept Authorization header:

**Find** (pattern):
```python
respx.get("https://example.opendental.com/api/v1/allergies?PatNum=12345").mock(
    return_value=httpx.Response(200, json=fixture_data)
)
```

**No change needed** - mocks already accept any headers. Just verify tests pass.

**Run**:
```bash
pytest tests/integration/ -v
```

**Expected**: All integration tests PASS

---

### Step 6: Update API Contract Documentation (5 min)

**File**: `specs/001-audit-data-cli/contracts/opendental-api.md`

**Find** (around line 8-12):
```markdown
## Base Configuration

**Base URL**: `https://{server}/api/v1/`  
**Authentication**: Custom Headers  
**Headers**: 
- `DeveloperKey: {developer_key}`
- `CustomerKey: {customer_key}`
```

**Replace with**:
```markdown
## Base Configuration

**Base URL**: `https://{server}/api/v1/`  
**Authentication**: ODFHIR Format  
**Authorization**: `Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}`  
**Content-Type**: `application/json`  
**TLS Version**: 1.2+

### Authentication Format

OpenDental FHIR API uses the ODFHIR authentication scheme:

```http
Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}
```

**Example**:
```http
Authorization: ODFHIR abc123def456/xyz789portal
```

Both keys are required:
- **Developer Key**: Obtained from OpenDental Developer Portal
- **Developer Portal Key**: Customer-specific authentication key
```

**Update all endpoint examples** (replace DeveloperKey/CustomerKey headers):

**Find**:
```http
GET /api/v1/procedurelogs?AptNum=67890 HTTP/1.1
Host: example.opendental.com
DeveloperKey: YOUR_DEVELOPER_KEY
CustomerKey: YOUR_CUSTOMER_KEY
Accept: application/json
```

**Replace with**:
```http
GET /api/v1/procedurelogs?AptNum=67890 HTTP/1.1
Host: example.opendental.com
Authorization: ODFHIR YOUR_DEVELOPER_KEY/YOUR_DEVELOPER_PORTAL_KEY
Accept: application/json
```

**Repeat for all 6 endpoints** in the contract document.

---

### Step 7: Run Full Test Suite (5 min)

```bash
# Run all tests
pytest --cov=opendental_cli --cov-report=term-missing

# Expected results:
# - All tests PASS
# - Coverage ≥90%
# - No new warnings
```

---

### Step 8: Manual Verification (15 min)

**Prerequisites**: Valid OpenDental credentials

**Step 8.1**: Configure credentials (if not already done)
```bash
opendental-cli config set-credentials
```

Enter:
- API Base URL: `https://your-server.opendental.com/api/v1`
- Developer Key: (your actual key)
- Developer Portal Key: (your actual portal key)
- Master Password: (create one for keyring encryption)

**Step 8.2**: Test API call
```bash
opendental-cli --patnum 12345 --aptnum 67890
```

**Expected output**:
- ✅ No 401 Unauthorized errors
- ✅ JSON output with patient/appointment data
- ✅ Exit code 0

**If 401 still occurs**:
1. Verify credentials are correct in OpenDental portal
2. Check API base URL is correct
3. Verify both keys are entered (no typos)
4. Check network connectivity to OpenDental server

---

## Validation Checklist

- [ ] Step 1: `get_auth_header()` updated in credential.py
- [ ] Step 2: CLI prompt changed to "Developer Portal Key"
- [ ] Step 3: Unit tests added and passing
- [ ] Step 4: Contract tests updated and passing
- [ ] Step 5: Integration tests passing
- [ ] Step 6: API contract documentation updated
- [ ] Step 7: Full test suite passes with ≥90% coverage
- [ ] Step 8: Manual test returns 200 OK

---

## Troubleshooting

### Issue: Unit tests fail with KeyError

**Symptom**: `KeyError: 'Authorization'`

**Cause**: Old test code expects DeveloperKey/CustomerKey

**Fix**: Update test to check for Authorization header

---

### Issue: 401 still occurs after fix

**Symptom**: Manual test still returns 401 Unauthorized

**Possible causes**:
1. **Wrong credentials**: Verify keys in OpenDental portal
2. **Wrong format**: Check Authorization header in debug logs
3. **Expired keys**: Request new keys from OpenDental
4. **Network issue**: Verify server URL is accessible

**Debug**:
```bash
# Add debug logging to api_client.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Run command and check logs for Authorization header
opendental-cli --patnum 12345 --aptnum 67890
```

---

### Issue: Tests pass but real API fails

**Symptom**: All tests green, but actual API returns error

**Cause**: Mocks don't validate header format

**Fix**: Add contract test that validates exact header format:
```python
def test_authorization_header_exact_format():
    """Verify exact ODFHIR format matches API expectations."""
    credential = APICredential(
        base_url="https://example.com/api/v1",
        developer_key="test_key",
        customer_key="portal_key"
    )
    
    auth = credential.get_auth_header()
    
    # Exact format check
    assert auth["Authorization"] == "ODFHIR test_key/portal_key"
    assert not auth["Authorization"].endswith(" ")  # No trailing space
    assert auth["Authorization"].count("/") == 1    # Exactly one slash
```

---

## Success Criteria

✅ **All tests pass**: Unit, contract, integration  
✅ **Coverage ≥90%**: No decrease in test coverage  
✅ **Manual test succeeds**: Real API returns 200 OK  
✅ **No PHI logged**: Authorization header uses SecretStr  
✅ **Documentation updated**: Contract docs reflect ODFHIR format  

---

## Next Steps

After successful implementation:

1. **Commit changes**:
   ```bash
   git add src/opendental_cli/models/credential.py
   git add src/opendental_cli/cli.py
   git add tests/
   git add specs/001-audit-data-cli/contracts/opendental-api.md
   git commit -m "fix: Use ODFHIR authorization format (fixes 401 errors)"
   ```

2. **Update README** (optional):
   - Add authentication section
   - Explain ODFHIR format
   - Document credential configuration

3. **Close related issues**:
   - Link to this spec in issue tracker
   - Mark 401 error issues as resolved

4. **Monitor**: Watch for any new authentication errors in production

---

## Time Breakdown

| Step | Task | Estimated | Actual |
|------|------|-----------|--------|
| 1 | Fix get_auth_header() | 5 min | |
| 2 | Update CLI prompts | 3 min | |
| 3 | Add unit tests | 5 min | |
| 4 | Update contract tests | 10 min | |
| 5 | Update integration tests | 10 min | |
| 6 | Update documentation | 5 min | |
| 7 | Run full test suite | 5 min | |
| 8 | Manual verification | 15 min | |
| **Total** | | **58 min** | |

---

**Status**: Ready for implementation  
**Priority**: P0 (Critical - blocks all API calls)  
**Risk**: Low (focused change with comprehensive tests)
