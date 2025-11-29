# Security Policy

## HIPAA Compliance

This CLI tool is designed with HIPAA compliance requirements in mind. Below are the security measures implemented to protect Protected Health Information (PHI).

### PHI Protection

#### 1. Credential Storage
- **Primary**: OS-native keyring with AES-256-GCM encryption
  - Windows: Credential Manager (DPAPI encryption)
  - macOS: Keychain (AES-256 encryption)
  - Linux: Secret Service API (encryption varies by backend)
- **Fallback**: Environment variables (with security warning displayed)
- **Never**: Plain text files, command history, or logs

#### 2. Audit Logging
- **Location**: `audit.log` with restrictive permissions (0o600)
- **Format**: JSON with UTC timestamps
- **Content**: Operation type, endpoint, HTTP status, duration
- **PHI Sanitization**: Automatic filtering of 21 PHI field types:
  - Patient identifiers (PatNum, FName, LName, SSN)
  - Dates (Birthdate, AptDateTime, DateStatement)
  - Contact info (Address, HmPhone, WkPhone, Email)
  - Medical data (ProcDescript, ToothNum, NoteText, Subscriber)

#### 3. PHI Redaction in Output
- `--redact-phi` flag replaces sensitive values with `[REDACTED]`
- Preserves JSON structure for debugging
- Safe for sharing with technical support

#### 4. Output File Permissions
- JSON output files created with 0o600 permissions (owner read/write only)
- Parent directories created with restrictive permissions
- File overwrite confirmation required (unless `--force` flag used)

### Network Security

#### TLS/SSL
- **Minimum TLS version**: 1.2
- **Certificate validation**: Enabled and enforced
- **Certificate pinning**: Not implemented (relies on OS certificate store)

#### API Communication
- **Timeout enforcement**: 45s total, 10s connect, 30s read
- **Retry logic**: 3 attempts with exponential backoff (1s, 2s, 4s) ± 20% jitter
- **Circuit breaker**: Opens after 5 consecutive failures, 60s cooldown
- **Rate limit handling**: Respects `Retry-After` header (429 responses)

### Authentication

#### API Keys Security (Developer Key & Customer Key)
- **Storage**: Both keys stored in OS keyring only (never in code, config files, or environment by default)
- **Transmission**: HTTPS only, both keys sent in custom headers (DeveloperKey and CustomerKey)
- **Rotation**: Manual via `opendental-cli config set-credentials`
- **Revocation**: Immediate effect (credentials fetched per execution)

### Known Limitations

#### 1. Python Memory Security
- **Issue**: Python does not zero memory after variable deletion
- **Impact**: Both API keys (Developer and Customer) and PHI may remain in process memory until garbage collection
- **Mitigation**: 
  - Credentials retrieved only when needed
  - Short-lived processes (CLI completes and exits)
  - Avoid long-running daemon mode
- **Recommendation**: Do not run on shared multi-user systems

#### 2. Terminal History
- **Issue**: Command-line arguments visible in shell history
- **Impact**: PatNum and AptNum may be logged to `~/.bash_history` or equivalent
- **Mitigation**: 
  - PatNum/AptNum are identifiers, not direct PHI
  - Use `HISTCONTROL=ignorespace` and prefix commands with space
  - Clear history after sensitive operations: `history -c`

#### 3. Process Listing
- **Issue**: Running processes visible via `ps` or Task Manager
- **Impact**: PatNum and AptNum visible to other users on same system
- **Mitigation**: 
  - Run on dedicated workstations
  - Short execution time (<60s typical)
  - Use sudo/admin privileges to restrict process visibility

#### 4. Log Aggregation
- **Issue**: If `audit.log` is sent to centralized logging system
- **Impact**: PHI sanitization must be verified in downstream systems
- **Mitigation**:
  - Review log aggregation pipeline for additional PHI filtering
  - Do not send raw audit logs to third-party services
  - Verify no PHI in logs before external transmission

### Vulnerability Reporting

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead, email security reports to: **security@opendental.example.com**

Include:
1. Description of vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if known)

We will acknowledge receipt within 48 hours and provide a remediation timeline.

### Security Audit History

| Date       | Auditor          | Scope                          | Findings |
|------------|------------------|--------------------------------|----------|
| 2025-11-29 | Development Team | Initial implementation review  | See constitution.md compliance checklist |

### Compliance Checklist

#### Article I: Code Quality & Maintainability
- ✅ All functions ≤30 lines
- ✅ Cyclomatic complexity ≤10
- ✅ Descriptive names, no abbreviations
- ✅ Comprehensive docstrings

#### Article II: HIPAA Security
- ✅ No PHI in logs (21 field types filtered)
- ✅ Audit trail with UTC timestamps
- ✅ File permissions 0o600
- ✅ OS keyring encryption (AES-256-GCM)

#### Article III: Defensive API Programming
- ✅ Timeout enforcement (45s total)
- ✅ Retry with exponential backoff (3 attempts)
- ✅ Circuit breaker (5 failures → 60s cooldown)
- ✅ Rate limit handling (429 with Retry-After)
- ✅ TLS 1.2+ with certificate validation

#### Article IV: Test Coverage
- ✅ 90%+ overall coverage (current: 90.61%)
- ✅ 100% mocked tests (no live API calls)
- ✅ Offline test execution

### Dependencies

All dependencies are vetted for security vulnerabilities. See `pyproject.toml` for pinned versions.

Key security-relevant dependencies:
- **keyring 24.3+**: OS-native credential storage
- **httpx 0.25+**: Modern HTTP client with async support
- **cryptography**: (transitive via keyring) Strong encryption
- **certifi**: Trusted CA certificates

Run vulnerability scan:
```bash
pip install safety
safety check --file requirements.txt
```

### Security Best Practices

#### For End Users
1. **Never share API keys** (Developer or Customer keys) via email, Slack, or unencrypted channels
2. **Use dedicated API keys** for this tool (not production admin keys)
3. **Rotate keys regularly** (every 90 days minimum)
4. **Audit access logs** in OpenDental API dashboard
5. **Use `--redact-phi` flag** when sharing output for troubleshooting
6. **Secure output files** - Delete after use, never email PHI

#### For Developers
1. **Never log PHI** - Use PHISanitizerProcessor for all logging
2. **Validate input** - PatNum/AptNum must be positive integers
3. **Test offline** - Use respx for HTTP mocking, never live API
4. **Review PRs** for PHI leakage in logs, errors, or output
5. **Update dependencies** regularly for security patches

### Encryption Details

#### Keyring Storage

- **Windows (DPAPI)**:
  - Encryption: AES-256-GCM
  - Key derivation: User login credentials + machine-specific key
  - Storage: Windows Registry (encrypted blobs)

- **macOS (Keychain)**:
  - Encryption: AES-256 (default keychain encryption)
  - Key derivation: User login password
  - Storage: `/Users/<user>/Library/Keychains/login.keychain-db`

- **Linux (Secret Service)**:
  - Encryption: AES-128 or AES-256 (depends on backend)
  - GNOME Keyring: Encrypted with user password
  - KWallet: Encrypted with user password or GPG key

#### Transport Layer

- **TLS 1.2+**: Minimum supported version
- **Cipher suites**: Determined by httpx/SSL library defaults
- **Certificate validation**: Enforced via `verify=True` in httpx client
- **Certificate store**: OS-native certificate trust store

### Incident Response

If PHI exposure occurs:

1. **Immediate Actions**:
   - Rotate compromised API keys (both Developer and Customer keys)
   - Delete exposed audit.log or output files
   - Document scope of exposure (which records, how many)

2. **Investigation**:
   - Review audit logs to identify when/how exposure occurred
   - Determine if additional records were accessed
   - Identify root cause (bug, misconfiguration, credential compromise)

3. **Notification** (if required by HIPAA Breach Notification Rule):
   - Notify affected individuals (if ≥500 records)
   - Report to HHS Office for Civil Rights
   - Follow organizational breach response plan

4. **Remediation**:
   - Apply fix to prevent recurrence
   - Update security documentation
   - Conduct security training for users

### Contact

- **Security issues**: security@opendental.example.com
- **General support**: support@opendental.example.com
- **Documentation**: https://github.com/opendental/audit-cli/wiki

Last updated: 2025-11-29
