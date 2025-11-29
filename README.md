# OpenDental Audit Data Retrieval CLI

A HIPAA-compliant command-line tool for retrieving audit data from OpenDental API endpoints. Securely fetches patient, appointment, treatment, billing, insurance, and clinical note data for compliance audits.

## Features

- **Secure Credential Storage**: Uses OS-native keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **HIPAA Compliance**: PHI sanitization in logs, optional PHI redaction in output, encrypted credential storage
- **Defensive API Integration**: Automatic retry with exponential backoff, circuit breaker pattern, timeout enforcement
- **Partial Failure Handling**: Continues execution when individual endpoints fail, returns partial data
- **Comprehensive Audit Trail**: All API calls logged with NO PHI data

## Requirements

- **Python 3.11+**
- **OS**: Windows 10+, macOS 10.15+, or Linux with keyring support (GNOME Keyring, KWallet, Secret Service)
- **OpenDental API**: Valid API credentials (Developer Key and Customer Key) with read access to patient, appointment, treatment, billing, insurance, and clinical data

## Installation

```bash
# Clone repository
git clone https://github.com/opendental/audit-cli.git
cd OpenDentalAuditDataRetrieval

# Install with pip
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure Credentials

```bash
# Interactive credential setup (stores in OS keyring)
opendental-cli config set-credentials

# Follow prompts:
# Enter OpenDental API Base URL: https://example.opendental.com/api/v1
# Enter Developer Key: your-developer-key-here
# Enter Customer Key: your-customer-key-here
# Select environment (production/staging/dev): production
```

**Alternative**: Use environment variables (less secure):

```bash
export OPENDENTAL_BASE_URL="https://example.opendental.com/api/v1"
export OPENDENTAL_DEVELOPER_KEY="your-developer-key-here"
export OPENDENTAL_CUSTOMER_KEY="your-customer-key-here"

# Windows PowerShell:
$env:OPENDENTAL_BASE_URL="https://example.opendental.com/api/v1"
$env:OPENDENTAL_DEVELOPER_KEY="your-developer-key-here"
$env:OPENDENTAL_CUSTOMER_KEY="your-customer-key-here"
```

### 2. Retrieve Audit Data

```bash
# Output to stdout (JSON)
opendental-cli --patnum 12345 --aptnum 67890

# Save to file (with restrictive 600 permissions)
opendental-cli --patnum 12345 --aptnum 67890 --output audit_data.json

# Redact PHI for debugging/support
opendental-cli --patnum 12345 --aptnum 67890 --redact-phi --output redacted.json
```

## Usage

### Basic Syntax

```bash
opendental-cli [OPTIONS]

Options:
  --patnum INTEGER    Patient Number (required, must be positive)
  --aptnum INTEGER    Appointment Number (required, must be positive)
  --output PATH       Output file path (default: stdout)
  --redact-phi        Replace PHI with [REDACTED] in output
  --force             Skip overwrite confirmation for existing files
  --help              Show this message and exit
```

### Subcommands

```bash
# Credential management
opendental-cli config set-credentials
```

### Exit Codes

- **0**: All endpoints succeeded
- **1**: All endpoints failed OR invalid input
- **2**: Partial success (some endpoints failed)

## Output Format

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

## Security Notes

### HIPAA Compliance

- **PHI Sanitization**: All logs automatically sanitize patient names, DOBs, SSNs, phone numbers
- **Credential Encryption**: Both API keys (Developer and Customer) stored in OS keyring with AES-256-GCM encryption
- **TLS 1.2+**: All API communication uses TLS 1.2+ with certificate validation (cannot be disabled)
- **File Permissions**: Output files created with mode 0o600 (owner read/write only)
- **Audit Trail**: Every API call logged to `audit.log` (NO PHI)

### Python Memory Zeroing Limitation

**Important**: Python's automatic garbage collection does not support explicit memory zeroing. Sensitive data (Developer Key, Customer Key, PHI) may remain in memory after use until garbage collection occurs.

**Recommendations**:
- Enable encrypted swap on your system
- Disable hibernation when handling PHI
- Run tool on systems with full-disk encryption
- Do not run tool on shared/multi-user systems

This is a known limitation of Python as a scripting language and is acceptable for CLI tools with proper system-level protections.

## Development

### Running Tests

```bash
# All tests (should complete in <10s)
pytest

# With coverage report
pytest --cov=opendental_cli --cov-report=html --cov-report=term

# Specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests
pytest tests/contract/       # API client contract tests

# Target: 90%+ overall coverage, 100% for security modules
```

### Code Quality

```bash
# Check cyclomatic complexity (target: ≤10 per function)
radon cc src/ -a

# Check lines per function (target: ≤30 lines)
radon raw src/ -s
```

### Mock Mode for Local Development

Set environment variable to use local fixtures without credentials:

```bash
export OPENDENTAL_MOCK_MODE=true
opendental-cli --patnum 12345 --aptnum 67890
```

## Architecture

### Core Modules

- **`cli.py`**: Click-based command-line interface
- **`credential_manager.py`**: Keyring integration for secure credential storage
- **`api_client.py`**: HTTPX-based API client with retry/timeout/circuit breaker
- **`phi_sanitizer.py`**: Structlog processor for PHI removal from logs
- **`phi_redactor.py`**: PHI redaction for output JSON
- **`audit_logger.py`**: Audit trail logging (non-PHI)
- **`circuit_breaker.py`**: Circuit breaker pattern implementation
- **`orchestrator.py`**: Coordinates multi-endpoint retrieval
- **`output_formatter.py`**: JSON formatting and file I/O

### Data Models (Pydantic)

- **Request Models**: `AuditDataRequest`, `APICredential`
- **Response Models**: `EndpointResponse`, `ConsolidatedAuditData`, `AuditLogEntry`
- **OpenDental Models**: `PatientResponse`, `AppointmentResponse`, `TreatmentResponse`, `BillingResponse`, `InsuranceResponse`, `ClinicalNotesResponse`

## Troubleshooting

### Keyring Not Available (Linux)

**Error**: `keyring.errors.NoKeyringError`

**Solution**:
```bash
# Install GNOME Keyring or KWallet
sudo apt-get install gnome-keyring  # Ubuntu/Debian
# Or use environment variables as fallback
```

### SSL Certificate Verification Failed

**Error**: `httpx.ConnectError: SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**: Constitution prohibits disabling certificate validation. Contact your OpenDental administrator to fix the certificate issue. Valid TLS 1.2+ certificate required.

### Permission Denied Writing Output

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
# Ensure write permissions in output directory
chmod u+w /path/to/output/directory

# Or specify writable location
opendental-cli --patnum 12345 --aptnum 67890 --output ~/audit_data.json
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, test requirements, and constitution compliance guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details

## Security

See [SECURITY.md](SECURITY.md) for HIPAA compliance details, security measures, and responsible disclosure policy.