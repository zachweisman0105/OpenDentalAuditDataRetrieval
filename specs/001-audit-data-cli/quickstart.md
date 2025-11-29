# Quickstart: OpenDental Audit Data Retrieval CLI

**Phase**: 1 - Design  
**Date**: 2025-11-29  
**Purpose**: Test scenarios and usage examples for development and validation

## Installation

```bash
# Clone repository
git clone <repo-url>
cd OpenDentalAuditDataRetrieval

# Install dependencies (Python 3.11+)
pip install -e .

# Or using Poetry
poetry install
```

---

## Configuration

### Option 1: Keyring (Recommended)

```bash
# Store credentials in OS keyring
opendental-cli config set-credentials

# Follow prompts:
# Enter OpenDental API Base URL: https://example.opendental.com/api/v1
# Enter API Key: your-api-key-here
# Select environment (production/staging/dev): production
```

### Option 2: Environment Variables (Fallback)

```bash
# Set environment variables (less secure)
export OPENDENTAL_BASE_URL="https://example.opendental.com/api/v1"
export OPENDENTAL_API_KEY="your-api-key-here"

# On Windows PowerShell:
$env:OPENDENTAL_BASE_URL="https://example.opendental.com/api/v1"
$env:OPENDENTAL_API_KEY="your-api-key-here"
```

---

## Basic Usage

### Retrieve Audit Data (stdout)

```bash
opendental-cli --patnum 12345 --aptnum 67890
```

**Output** (JSON to stdout):
```json
{
  "request": {
    "patnum": 12345,
    "aptnum": 67890,
    "output_file": null,
    "redact_phi": false
  },
  "success": {
    "patient": {...},
    "appointment": {...},
    "treatment": {...},
    "billing": {...},
    "insurance": {...},
    "clinical_notes": {...}
  },
  "failures": [],
  "total_endpoints": 6,
  "successful_count": 6,
  "failed_count": 0,
  "retrieval_timestamp": "2025-11-29T10:30:00Z"
}
```

### Save to File

```bash
opendental-cli --patnum 12345 --aptnum 67890 --output audit_data.json
```

**Result**: Creates `audit_data.json` with 600 permissions (owner read/write only)

### Redact PHI

```bash
opendental-cli --patnum 12345 --aptnum 67890 --redact-phi --output audit_data_redacted.json
```

**Output** (PHI replaced with `[REDACTED]`):
```json
{
  "success": {
    "patient": {
      "PatNum": 12345,
      "FName": "[REDACTED]",
      "LName": "[REDACTED]",
      "Birthdate": "[REDACTED]",
      "SSN": "[REDACTED]",
      ...
    }
  }
}
```

---

## Test Scenarios

### Scenario 1: Happy Path (All Endpoints Succeed)

**Setup**:
- Mock all 6 endpoints to return 200 OK
- Use fixtures: `patient_success.json`, `appointment_success.json`, etc.

**Execution**:
```bash
pytest tests/integration/test_golden_path.py::test_all_endpoints_success
```

**Expected**:
- Exit code: 0
- JSON output contains all 6 endpoints in `success` dict
- `failures` list is empty
- Audit log has 6 entries (one per endpoint)

---

### Scenario 2: Partial Failure (Billing Endpoint Down)

**Setup**:
- Mock 5 endpoints to return 200 OK
- Mock billing endpoint to return 503 Service Unavailable

**Execution**:
```bash
pytest tests/integration/test_partial_failure.py::test_one_endpoint_fails
```

**Expected**:
- Exit code: 2 (partial success)
- JSON output:
  ```json
  {
    "success": {
      "patient": {...},
      "appointment": {...},
      "treatment": {...},
      "insurance": {...},
      "clinical_notes": {...}
    },
    "failures": [
      {"endpoint": "billing", "error": "Service unavailable (503)"}
    ],
    "successful_count": 5,
    "failed_count": 1
  }
  ```

---

### Scenario 3: Complete Failure (All Endpoints Timeout)

**Setup**:
- Mock all endpoints to raise `asyncio.TimeoutError` after 45s

**Execution**:
```bash
pytest tests/integration/test_complete_failure.py::test_all_endpoints_timeout
```

**Expected**:
- Exit code: 1 (complete failure)
- JSON output:
  ```json
  {
    "success": {},
    "failures": [
      {"endpoint": "patient", "error": "Request timeout (45s)"},
      {"endpoint": "appointment", "error": "Request timeout (45s)"},
      ...
    ],
    "successful_count": 0,
    "failed_count": 6
  }
  ```

---

### Scenario 4: Invalid PatNum/AptNum

**Execution**:
```bash
opendental-cli --patnum 0 --aptnum 67890
```

**Expected**:
- Exit immediately with error message:
  ```
  Error: PatNum and AptNum must be positive integers
  ```
- Exit code: 1
- No API calls made

---

### Scenario 5: Patient Not Found (404)

**Setup**:
- Mock patient endpoint to return 404
- Other endpoints return 200 OK

**Expected**:
- Exit code: 2 (partial success)
- Patient endpoint in `failures` with "Patient not found (404)"
- Other endpoints in `success`

---

### Scenario 6: Credentials Not Configured

**Execution**:
```bash
# Without credentials in keyring or env variables
opendental-cli --patnum 12345 --aptnum 67890
```

**Expected**:
- Exit immediately with error:
  ```
  Error: No credentials configured.
  
  Please run: opendental-cli config set-credentials
  
  Or set environment variables:
  export OPENDENTAL_BASE_URL="https://your-server/api/v1"
  export OPENDENTAL_API_KEY="your-api-key"
  ```
- Exit code: 1
- No API calls made

---

### Scenario 7: Rate Limit Hit (429)

**Setup**:
- Mock first request to return 429 with `Retry-After: 5`
- Mock retry after 5s to return 200 OK

**Expected**:
- Display message: "API rate limit reached, retrying in 5s"
- Wait 5 seconds
- Retry request successfully
- Exit code: 0

---

### Scenario 8: Circuit Breaker Opens

**Setup**:
- Mock endpoint to return 500 five times in a row
- Mock 6th request to return 200 (after cooldown)

**Expected**:
- After 5 failures, circuit opens
- Subsequent requests fail fast without API call for 60s
- After 60s cooldown, half-open state allows probe request
- Probe succeeds, circuit closes

**Test**:
```bash
pytest tests/unit/test_circuit_breaker.py::test_circuit_opens_after_threshold
```

---

### Scenario 9: Malformed JSON Response

**Setup**:
- Mock endpoint to return invalid JSON: `{"patient": incomplete...`

**Expected**:
- Pydantic ValidationError caught
- Endpoint marked as failed with "Invalid response format"
- Continue with other endpoints

---

### Scenario 10: PHI Sanitization in Logs

**Setup**:
- Enable debug logging
- Run retrieval with valid PatNum

**Verification**:
```bash
# Check audit log contains no PHI
grep -E "12345|John|Doe|1985-03-15" audit.log

# Expected: No matches (all PHI sanitized)
```

**Test**:
```bash
pytest tests/unit/test_phi_sanitizer.py::test_sanitizes_all_phi_patterns
```

---

## Mock Mode for Development

Run CLI against local fixtures without credentials:

```bash
# Set mock mode (feature for development)
export OPENDENTAL_MOCK_MODE=true

opendental-cli --patnum 12345 --aptnum 67890
```

**Behavior**:
- Loads responses from `tests/fixtures/` instead of making API calls
- No credentials required
- Enables local UI/output development

---

## Testing with pytest

### Run Full Test Suite

```bash
# All tests (should complete in <10s)
pytest

# With coverage report
pytest --cov=opendental_cli --cov-report=html --cov-report=term

# Target: 90%+ overall, 100% for security modules
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Contract tests (API client behavior)
pytest tests/contract/

# Single test file
pytest tests/unit/test_phi_sanitizer.py
```

### Test Fixtures

All fixtures in `tests/fixtures/`:

```
tests/fixtures/
├── patient_12345.json          # Valid patient response
├── patient_404.json            # Patient not found
├── appointment_67890.json      # Valid appointment
├── appointment_503.json        # Service unavailable
├── treatment_success.json      # Valid treatment history
├── treatment_empty.json        # No procedures
├── billing_success.json        # Valid billing records
├── billing_timeout.json        # Simulated timeout
├── insurance_success.json      # Valid claims
├── insurance_malformed.json    # Invalid JSON structure
├── clinical_notes_success.json # Valid progress notes
└── clinical_notes_empty.json   # No notes available
```

---

## Example Test (Golden Path)

```python
# tests/integration/test_golden_path.py
import pytest
import respx
from httpx import Response
from opendental_cli import cli
from tests.fixtures import load_fixture

@pytest.mark.asyncio
@respx.mock
async def test_golden_path_all_success(tmp_path):
    """Test successful retrieval from all endpoints."""
    
    # Setup mocks
    base_url = "https://example.com/api/v1"
    
    respx.get(f"{base_url}/patients/12345").mock(
        return_value=Response(200, json=load_fixture("patient_12345.json"))
    )
    respx.get(f"{base_url}/appointments/67890").mock(
        return_value=Response(200, json=load_fixture("appointment_67890.json"))
    )
    # ... mock other endpoints
    
    # Execute
    output_file = tmp_path / "audit_data.json"
    result = cli.main(["--patnum", "12345", "--aptnum", "67890", "--output", str(output_file)])
    
    # Assertions
    assert result.exit_code == 0
    assert output_file.exists()
    
    data = json.loads(output_file.read_text())
    assert data["successful_count"] == 6
    assert data["failed_count"] == 0
    assert "patient" in data["success"]
    assert "appointment" in data["success"]
```

---

## Audit Log Review

After running CLI, check audit log:

```bash
# View audit log (no PHI)
cat audit.log

# Example entry:
{
  "timestamp": "2025-11-29T10:30:00Z",
  "operation_type": "fetch_patient",
  "endpoint": "/patients/REDACTED",
  "http_status": 200,
  "success": true,
  "duration_ms": 245.3,
  "error_category": null,
  "user_id": "system_user"
}
```

**Verification**: No PatNum, patient names, dates, or other PHI in logs

---

## Common Issues

### Issue: Keyring Not Available (Linux)

**Error**: `keyring.errors.NoKeyringError`

**Solution**:
```bash
# Install GNOME Keyring or KWallet
sudo apt-get install gnome-keyring  # Ubuntu/Debian
# Or use environment variables as fallback
```

### Issue: Permission Denied Writing Output File

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
# Ensure write permissions in output directory
chmod u+w /path/to/output/directory

# Or specify writable location
opendental-cli --patnum 12345 --aptnum 67890 --output ~/audit_data.json
```

### Issue: SSL Certificate Verification Failed

**Error**: `httpx.ConnectError: SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**:
```bash
# Ensure valid SSL certificate on OpenDental server
# Constitution prohibits disabling certificate validation
# Contact OpenDental administrator to fix certificate issue
```

---

## Performance Benchmarks

Expected performance on typical hardware:

- **All endpoints success**: 3-5 seconds (6 sequential requests, ~500-800ms each)
- **With retry (one 503)**: 5-7 seconds (includes 1s initial delay)
- **With rate limit (429)**: 8-12 seconds (includes Retry-After wait)
- **Test suite execution**: <10 seconds (fully mocked)

---

## Next Steps

After validating quickstart scenarios:

1. Run `/speckit.tasks` to generate implementation task list
2. Begin implementation starting with P1 user stories
3. Use fixtures from quickstart for TDD workflow
4. Verify constitution compliance at each milestone
