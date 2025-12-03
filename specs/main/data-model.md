# Data Model: ODFHIR Authorization Header

**Date**: 2025-12-02  
**Phase**: 1 - Design  
**Status**: Ready for Implementation

## Overview

This document defines the data model changes required to fix the OpenDental FHIR authorization format. The core change is in how authentication credentials are combined into an HTTP header.

---

## Entity: APICredential

**Location**: `src/opendental_cli/models/credential.py`

### Fields

| Field | Type | Description | Changes |
|-------|------|-------------|---------|
| `base_url` | HttpUrl | OpenDental API base URL | ✅ No change |
| `developer_key` | SecretStr | Developer Key (first part of ODFHIR auth) | ✅ No change |
| `customer_key` | SecretStr | Developer Portal Key (second part of ODFHIR auth) | ✅ No change |
| `environment` | str | Environment name (production/staging/dev) | ✅ No change |

**Note**: Field names remain unchanged to preserve compatibility with existing credential storage in OS keyring. Only the method that constructs the authorization header changes.

### Method: get_auth_header()

**Purpose**: Generate HTTP authorization header for OpenDental FHIR API requests

**Current Implementation** (INCORRECT):
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

**New Implementation** (CORRECT):
```python
def get_auth_header(self) -> dict[str, str]:
    """Generate OpenDental FHIR Authorization header.
    
    OpenDental FHIR API uses the ODFHIR authentication scheme with format:
        Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}
    
    Both keys are required:
    - DeveloperKey: Issued by OpenDental Developer Portal
    - DeveloperPortalKey: Customer-specific portal authentication key
    
    SecretStr ensures credentials are not leaked in logs or error messages.
    
    Returns:
        Single-entry dict with Authorization header in ODFHIR format
        
    Example:
        {"Authorization": "ODFHIR abc123def456/xyz789portal"}
    """
    developer_key = self.developer_key.get_secret_value()
    portal_key = self.customer_key.get_secret_value()
    
    return {
        "Authorization": f"ODFHIR {developer_key}/{portal_key}"
    }
```

### Return Value Changes

**Before**:
```python
{
    "DeveloperKey": "abc123def456",
    "CustomerKey": "xyz789portal"
}
```

**After**:
```python
{
    "Authorization": "ODFHIR abc123def456/xyz789portal"
}
```

### Security Considerations

1. **No Logging**: Authorization header uses `SecretStr`, preventing accidental logging
2. **Runtime Construction**: Header assembled on-demand, never stored
3. **Secure Deletion**: Both `developer_key` and `portal_key` variables are local scope, garbage collected after return
4. **No Plain Text**: Credentials remain encrypted in keyring, only decrypted at request time

---

## HTTP Header Format

### ODFHIR Authentication Scheme

**Scheme**: `ODFHIR` (OpenDental FHIR)  
**Format**: `ODFHIR {DeveloperKey}/{DeveloperPortalKey}`  
**Header**: `Authorization`

### Example Request

```http
GET /api/v1/allergies?PatNum=12345 HTTP/1.1
Host: example.opendental.com
Authorization: ODFHIR dev_abc123def456/portal_xyz789
Accept: application/json
Content-Type: application/json
```

### Format Validation Rules

1. **Prefix**: Must start with `ODFHIR ` (with space after ODFHIR)
2. **Separator**: Keys must be separated by `/` (forward slash)
3. **No Spaces**: No spaces between keys and separator
4. **Case Sensitive**: Keys are case-sensitive
5. **No Encoding**: Keys are used as-is, no URL encoding or base64

---

## Integration Points

### API Client Usage

**Location**: `src/opendental_cli/api_client.py`

**Current** (working correctly):
```python
self.client = httpx.AsyncClient(
    base_url=credential.base_url,
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        **credential.get_auth_header(),  # Spreads auth header into client
    },
    timeout=httpx.Timeout(10.0, read=30.0, write=10.0, pool=5.0),
    verify=True,
)
```

**No changes needed**: The spreading mechanism (`**credential.get_auth_header()`) works correctly. It will now spread the single Authorization header instead of two custom headers.

### Credential Storage

**Location**: `src/opendental_cli/credential_manager.py`

**No changes needed**: Credentials are stored and retrieved with the same field names:
- Keyring key: `{environment}_developer_key` → stores first part of ODFHIR
- Keyring key: `{environment}_customer_key` → stores second part of ODFHIR

The only change is how these values are combined when constructing the HTTP header.

---

## Validation Rules

### Pre-Request Validation

Before sending any API request, validate:

1. **Developer Key Present**: `developer_key` is not None or empty
2. **Portal Key Present**: `customer_key` is not None or empty
3. **No Slash in Keys**: Neither key contains `/` character (would break format)
4. **No Spaces in Keys**: Neither key contains leading/trailing spaces

**Implementation** (optional, can add to get_auth_header()):
```python
def get_auth_header(self) -> dict[str, str]:
    """Generate OpenDental FHIR Authorization header."""
    developer_key = self.developer_key.get_secret_value().strip()
    portal_key = self.customer_key.get_secret_value().strip()
    
    # Validation (optional but recommended)
    if not developer_key or not portal_key:
        raise ValueError("Both Developer Key and Portal Key are required")
    if "/" in developer_key or "/" in portal_key:
        raise ValueError("Keys cannot contain '/' character")
    
    return {
        "Authorization": f"ODFHIR {developer_key}/{portal_key}"
    }
```

### Post-Request Validation

After receiving API response:

1. **401 Unauthorized**: Authorization header rejected by API
   - Possible causes: Invalid key format, expired keys, incorrect keys
   - User message: "Authentication failed. Verify your Developer Key and Portal Key are correct."

2. **403 Forbidden**: Authorization accepted but insufficient permissions
   - User message: "Access denied. Your credentials lack permission for this operation."

3. **200 OK**: Authorization successful
   - No action needed

---

## Testing Requirements

### Unit Tests

**Test 1: Verify ODFHIR Format**
```python
def test_get_auth_header_returns_odfhir_format():
    credential = APICredential(
        base_url="https://example.com/api/v1",
        developer_key="test_dev_key",
        customer_key="test_portal_key"
    )
    
    auth = credential.get_auth_header()
    
    assert "Authorization" in auth
    assert auth["Authorization"] == "ODFHIR test_dev_key/test_portal_key"
```

**Test 2: Verify Old Headers Removed**
```python
def test_get_auth_header_no_custom_headers():
    credential = APICredential(
        base_url="https://example.com/api/v1",
        developer_key="key1",
        customer_key="key2"
    )
    
    auth = credential.get_auth_header()
    
    assert "DeveloperKey" not in auth
    assert "CustomerKey" not in auth
    assert len(auth) == 1  # Only Authorization header
```

**Test 3: Verify SecretStr Protection**
```python
def test_get_auth_header_uses_secret_values():
    """Verify method extracts actual values from SecretStr."""
    credential = APICredential(
        base_url="https://example.com/api/v1",
        developer_key="secret_dev",
        customer_key="secret_portal"
    )
    
    auth = credential.get_auth_header()
    
    # SecretStr should be resolved to actual string
    assert "SecretStr" not in auth["Authorization"]
    assert "secret_dev" in auth["Authorization"]
    assert "secret_portal" in auth["Authorization"]
```

### Contract Tests

**Test: Verify Authorization Header Sent**
```python
@respx.mock
async def test_api_client_sends_odfhir_authorization():
    credential = APICredential(
        base_url="https://example.com/api/v1",
        developer_key="test_dev",
        customer_key="test_portal"
    )
    
    client = OpenDentalAPIClient(credential)
    
    respx.get("https://example.com/api/v1/allergies?PatNum=12345").mock(
        return_value=httpx.Response(200, json={})
    )
    
    await client.fetch_allergies(12345)
    
    # Verify correct header sent
    request = respx.calls.last.request
    assert "Authorization" in request.headers
    assert request.headers["Authorization"] == "ODFHIR test_dev/test_portal"
```

---

## Migration Impact

### No Credential Migration Needed

**Reason**: Field names (`developer_key`, `customer_key`) remain unchanged in both:
- Credential model (credential.py)
- Keyring storage (credential_manager.py)

Existing credentials stored in OS keyring will work immediately with new header format.

### User Experience

**Before Fix**:
```bash
$ opendental-cli --patnum 12345 --aptnum 67890
Error: All endpoints failed with 401 Unauthorized
```

**After Fix**:
```bash
$ opendental-cli --patnum 12345 --aptnum 67890
✓ Retrieved 6 endpoints successfully
[... JSON output ...]
```

No need for users to reconfigure credentials or re-run `config set-credentials`.

---

## Documentation Updates

### API Contract Document

**File**: `specs/001-audit-data-cli/contracts/opendental-api.md`

**Update Base Configuration Section**:
```markdown
## Base Configuration

**Base URL**: `https://{server}/api/v1/`  
**Authentication**: ODFHIR Format  
**Authorization Header**: `Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}`  
**Content-Type**: `application/json`  
**TLS Version**: 1.2+  

### Example Request

```http
GET /api/v1/allergies?PatNum=12345 HTTP/1.1
Host: example.opendental.com
Authorization: ODFHIR dev_abc123/portal_xyz789
Accept: application/json
```

### Obtaining Credentials

1. **Developer Key**: Obtain from OpenDental Developer Portal
2. **Developer Portal Key**: Customer-specific portal authentication key

Both keys are required for all API requests.
```

---

## Rollback Plan

If the ODFHIR format proves incorrect after implementation:

1. **Quick Rollback**: Git revert the single commit that changes `get_auth_header()`
2. **Investigation**: Capture actual working request from user or OpenDental support
3. **Correction**: Update format based on real evidence
4. **Re-deployment**: Apply corrected format

**Risk**: Low - format is clearly specified by user as `ODFHIR key1/key2`

---

## Summary

**Core Change**: Single method modification in `credential.py::get_auth_header()`

**Impact**:
- ✅ Fixes 401 Unauthorized errors on all endpoints
- ✅ No credential migration needed
- ✅ No breaking changes to CLI interface
- ✅ Maintains HIPAA compliance (SecretStr protection)

**Implementation Complexity**: Low (30 minutes including tests)

**Risk Level**: Low (focused change, comprehensive test coverage)

---

## Approval Checklist

- [X] Data model change documented
- [X] Security implications reviewed (no new risks)
- [X] Testing requirements defined
- [X] Migration impact assessed (no migration needed)
- [X] Rollback plan defined
- [X] Documentation updates identified

**Status**: Ready for implementation (Phase 2)
