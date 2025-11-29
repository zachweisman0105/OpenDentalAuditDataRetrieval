<!--
  SYNC IMPACT REPORT
  ==================
  Version Change: 1.0.0 → 1.1.0
  Rationale: MINOR version bump for material expansion of security and testing principles
  
  Modified Principles:
    - Article II: Added encryption-at-rest, keyring integration, and data destruction laws
    - Article IV: Strengthened mocking requirements, added coverage targets, explicit API call prohibition
  
  Added Sections:
    - Security Requirements: Encryption standards and keyring implementation requirements
  
  Removed Sections: None
  
  Templates Requiring Updates:
    ✅ plan-template.md - Constitution Check includes encryption/keyring validation
    ✅ spec-template.md - Security requirements reflect encryption mandates
    ✅ tasks-template.md - Test tasks emphasize mock-only approach
  
  Follow-up TODOs: None
-->

# OpenDental Audit Data Retrieval CLI - Constitution

## Core Principles

### Article I: Cognitive Load & Readability

**Mandate**: Code must optimize for human comprehension and debuggability above all else.

**Non-Negotiable Laws**:

1. **Function Atomicity Rule**: Every function MUST perform exactly one logical operation. Functions exceeding 30 lines of code require explicit justification in code review.

2. **Anti-Monolith Law**: The CLI entry point (`main` or equivalent) MUST NOT contain business logic. Its sole responsibility is argument parsing, function orchestration, and output formatting.

3. **Naming Precision Standard**: Functions, variables, and modules MUST use descriptive names that eliminate the need for inline comments to understand intent. Abbreviations are prohibited except for universally recognized acronyms (API, CLI, JSON, PHI).

4. **Single Responsibility Enforcement**: Each module MUST encapsulate one cohesive domain concept. Examples of valid domains: `api_client`, `credential_manager`, `patient_data`, `output_formatter`. Counter-examples: `utils`, `helpers`, `common`.

5. **Dependency Inversion Requirement**: Business logic MUST NOT directly import HTTP libraries or credential stores. All external dependencies MUST be injected through interfaces or dependency injection patterns.

6. **Cyclomatic Complexity Limit**: No function may exceed a cyclomatic complexity of 10. Complex conditional logic MUST be decomposed into named predicate functions.

**Rationale**: PHI auditing requires absolute clarity during incident investigation. Obscure code impedes compliance reviews and extends response times during security events.

---

### Article II: HIPAA-Compliant Security Posture

**Mandate**: Zero tolerance for PHI leakage. Every data handling decision assumes hostile observation.

**Non-Negotiable Laws**:

1. **Credential Isolation Law**: API credentials MUST be sourced exclusively from:
   - Environment variables (preferred for CI/CD)
   - System keyring/credential stores (Windows Credential Manager, macOS Keychain, Linux Secret Service)
   - NEVER from command-line arguments, plain-text configuration files, or hardcoded values
   - Keyring integration MUST use established libraries (`keyring` for Python, `CredentialManager` for .NET)

2. **Encryption-at-Rest Mandate**: Any persistent storage of PHI or credentials MUST use encryption:
   - AES-256-GCM or equivalent AEAD cipher for data at rest
   - Keys MUST be derived from system keyring or HSM, never stored alongside encrypted data
   - Temporary files containing PHI MUST be encrypted and securely deleted after use
   - Audit logs containing operational metadata MUST use restrictive file permissions (600 Unix, ACL on Windows)

3. **Logging Sanitization Standard**: All logging, error messages, and console output MUST pass through a sanitization layer that strips:
   - Patient identifiers (PatNum, names, dates of birth)
   - Appointment details (dates, provider names)
   - Raw API responses containing PHI
   - Authentication tokens or credentials

4. **Error Handling Protocol**: Exceptions MUST log non-PHI context (operation type, timestamp, error category) while displaying only generic user-facing messages. Detailed error traces MUST be written to a secure audit log with restricted permissions.

5. **Output Redaction Rule**: JSON output MUST support a `--redact-phi` flag that replaces sensitive fields with `[REDACTED]` placeholders while preserving data structure for debugging.

6. **Memory Management Law**: PHI-containing objects MUST be explicitly cleared from memory after use. In languages without automatic memory management, employ secure deletion patterns (e.g., zero-fill before deallocation).

7. **Data Destruction Protocol**: When PHI is no longer needed:
   - In-memory data structures MUST be overwritten with zeros before deallocation
   - Temporary files MUST be securely deleted using multi-pass overwrite (3+ passes) or OS secure deletion APIs
   - Cache entries containing PHI MUST have explicit TTL and automatic purging

8. **Audit Trail Mandate**: Every API call MUST generate an audit log entry containing:
   - Operation timestamp (UTC)
   - User identifier (non-PHI)
   - Operation type and endpoint
   - Success/failure status
   - NO actual PHI data

9. **Transmission Security**: All API communication MUST use TLS 1.2+ with certificate validation enabled. Certificate validation MUST NOT be disabled even in development environments.

10. **Keyring Integration Requirement**: Credential management MUST:
   - Use OS-native keyring as primary credential store
   - Implement fallback to environment variables only when keyring unavailable (document security implications)
   - Provide CLI command to store credentials: `opendental-cli config set-credentials`
   - Never prompt for credentials in non-interactive environments (fail with clear error)

**Rationale**: HIPAA violations carry penalties up to $50,000 per record. Design assumes logs, error messages, and console history are discoverable in breach investigations.

---

### Article III: Defensive API Integration

**Mandate**: OpenDental API calls MUST never assume happy-path execution.

**Non-Negotiable Laws**:

1. **Timeout Discipline**: Every HTTP request MUST specify:
   - Connection timeout: 10 seconds
   - Read timeout: 30 seconds
   - Total request timeout: 45 seconds

2. **Retry Policy Standard**: Failed requests MUST implement exponential backoff with:
   - Maximum 3 retry attempts
   - Initial delay: 1 second
   - Backoff multiplier: 2x
   - Jitter: ±20% randomization to prevent thundering herd
   - Retry only on network errors and 5xx responses (NOT 4xx client errors)

3. **Rate Limit Handling**: HTTP 429 responses MUST:
   - Extract `Retry-After` header if present
   - Wait specified duration before retrying
   - If header absent, apply standard exponential backoff
   - Emit clear user feedback: "API rate limit reached, retrying in {seconds}s"

4. **Partial Failure Isolation**: Multi-endpoint operations (e.g., fetching patient + appointment data) MUST:
   - Continue fetching remaining endpoints when one fails
   - Return partial results with explicit failure annotations
   - Use JSON structure: `{"success": [...], "failures": [{"endpoint": "...", "error": "..."}]}`

5. **Circuit Breaker Pattern**: After 5 consecutive failures to the same endpoint, MUST:
   - Enter "open" state for 60 seconds
   - Fail fast without attempting requests during open state
   - Attempt single "half-open" probe request after cooldown
   - Reset to "closed" on success or extend open period on continued failure

6. **Response Validation Law**: All API responses MUST be validated against expected schema before processing. Missing required fields MUST be treated as errors, not silent failures.

7. **Idempotency Awareness**: Read-only GET requests may be safely retried. POST/PUT/DELETE operations MUST NOT be automatically retried without explicit idempotency guarantees from API documentation.

**Rationale**: Healthcare APIs experience unpredictable load from clinical workflows. Network volatility is normal; graceful degradation preserves data integrity and user trust.

---

### Article IV: Developer Experience & Testability

**Mandate**: Testing overhead MUST NOT impede development velocity.

**Non-Negotiable Laws**:

1. **Absolute API Call Prohibition**: All automated tests MUST use fake/mocked responses. This is NON-NEGOTIABLE:
   - NO actual HTTP requests to OpenDental API during test execution
   - NO network sockets opened (except for local test servers if needed)
   - Tests MUST pass in fully offline environments
   - CI/CD pipelines MUST NOT have access to production credentials
   - Violation detection: Network monitoring tools in CI to fail builds on external connections

2. **Mock Implementation Strategy**:
   - Create `tests/fixtures/` directory containing sample JSON responses for each endpoint
   - Use a fixture-loading pattern: `load_fixture("patient_12345.json")`
   - Fixtures MUST include both success cases and error scenarios (404, 500, malformed JSON)

3. **Dependency Injection Requirement**: The API client MUST be injectable to enable test doubles:
   ```python
   # Compliant pattern
   def fetch_patient_data(api_client: APIClient, pat_num: int) -> PatientData:
       return api_client.get(f"/patients/{pat_num}")
   
   # Test usage
   mock_client = MockAPIClient(fixture="patient_12345.json")
   result = fetch_patient_data(mock_client, 12345)
   ```

4. **Test Organization Law**: Tests MUST be organized by:
   - `tests/unit/` - Pure function logic (no I/O)
   - `tests/integration/` - Multi-component workflows with mocked external dependencies
   - `tests/contract/` - API client behavior validation (using fixtures, not live API)
   - `tests/e2e/` - OPTIONAL manual smoke tests against non-production API (requires explicit `--e2e` flag)

5. **Fast Feedback Loop Standard**: The full test suite MUST execute in under 10 seconds. Tests exceeding this duration indicate insufficient mocking.

6. **Maximum Coverage Target**: Aim for the highest practical test coverage:
   - Target: 90%+ line coverage for business logic
   - 100% coverage for security-critical code (credential handling, PHI sanitization, encryption)
   - Coverage measurement MUST be part of CI/CD pipeline
   - Decreasing coverage trends MUST be flagged in code review

7. **Fake Data Generation**: Test fixtures MUST:
   - Use realistic but synthetic PHI (generated via faker libraries)
   - Include edge cases: empty strings, Unicode characters, very long values
   - Represent actual OpenDental API response schemas accurately
   - Be versioned alongside code (fixtures are documentation)

8. **Error Scenario Coverage**: For every happy-path test, MUST include at least one unhappy-path test covering:
   - Network timeouts
   - Malformed API responses
   - HTTP error codes (400, 401, 404, 500, 503)
   - Partial failures in multi-endpoint operations

9. **Documentation Through Tests**: Each API integration MUST include a "golden path" integration test that serves as executable documentation of expected behavior.

10. **Test Isolation Enforcement**: Every test MUST:
   - Reset state before execution (no test order dependencies)
   - Use dependency injection for all external dependencies
   - Mock file system operations for tests not specifically testing I/O
   - Not rely on global variables or singletons

11. **Local Development Iteration**: Developers MUST be able to:
   - Run tests without any external service dependencies
   - Run the CLI against mock data for UI/output development
   - Validate credential loading without production credentials

**Rationale**: API-dependent testing creates fragile test suites vulnerable to external service instability. More critically, live API calls in tests risk PHI exposure in CI logs, test reports, and developer environments. Comprehensive mocking with maximum coverage ensures 100% HIPAA compliance in testing while enabling rapid iteration and TDD workflows.

---

## Security Requirements

**Scope**: Additional security constraints beyond Article II for 100% HIPAA compliance.

1. **Encryption Standards**: All cryptographic operations MUST follow:
   - **Symmetric encryption**: AES-256-GCM (preferred) or ChaCha20-Poly1305
   - **Key derivation**: PBKDF2 (100k+ iterations), Argon2id (preferred), or scrypt
   - **Random number generation**: OS-provided cryptographically secure RNG (e.g., `secrets` module in Python)
   - **Prohibited algorithms**: DES, 3DES, RC4, MD5 for security purposes, SHA-1 for signatures
   - Use established cryptography libraries (e.g., `cryptography` in Python, `.NET Crypto`) - never implement custom crypto

2. **Keyring Implementation Requirements**:
   - **Primary**: Integrate with OS keyring using cross-platform library (e.g., Python `keyring` package)
   - **Service name**: Use consistent identifier: `opendental-audit-cli`
   - **Key naming**: Structure as `{environment}.api_key` (e.g., `production.api_key`, `staging.api_key`)
   - **Environment isolation**: Production and non-production credentials MUST use different keyring entries
   - **Credential rotation**: Support updating credentials without code changes
   - **Error handling**: Fail securely when keyring unavailable (no silent fallback to insecure storage)

3. **Dependency Auditing**: All third-party dependencies MUST be scanned for known vulnerabilities using automated tooling (e.g., `pip-audit`, `safety`, `snyk`). Critical/high severity vulnerabilities MUST be remediated within 7 days of disclosure.

4. **Least Privilege Principle**: File system operations MUST:
   - Write output to user-specified paths only (no hidden system directories)
   - Create files with restrictive permissions (600 on Unix, equivalent on Windows)
   - Never require elevated privileges (sudo/admin rights)

5. **Input Validation**: Command-line arguments MUST be validated:
   - `PatNum` and `AptNum` MUST be positive integers
   - File paths MUST be sanitized to prevent directory traversal attacks
   - Reject all input containing SQL/command injection patterns (even though we're not executing SQL, this establishes defensive habits)

6. **Secrets Management**:
   - NO placeholder credentials in documentation examples
   - README MUST provide clear instructions for secure credential configuration via keyring
   - Example `.env.template` file MUST contain placeholder values like `OPENDENTAL_API_KEY=your_key_here`
   - Documentation MUST emphasize keyring as primary method, environment variables as fallback only

7. **HIPAA Compliance Verification**: Before any release:
   - Run security audit checklist covering all Articles
   - Verify no PHI in logs, error messages, or test outputs
   - Confirm encryption enabled for all data at rest
   - Validate keyring integration functional on target platforms (Windows, macOS, Linux)
   - Document compliance evidence in release notes

---

## Development Workflow

**Scope**: Process requirements for maintaining constitutional compliance.

1. **Code Review Gate**: All pull requests MUST include:
   - Explicit verification that PHI is not logged or displayed inappropriately
   - Confirmation that new functions adhere to the 30-line guideline
   - Validation that error handling includes retry logic where applicable

2. **Test Coverage Enforcement**: New code submissions MUST include:
   - Unit tests for all business logic functions
   - Integration tests for multi-step workflows
   - At least one error-scenario test per function

3. **Static Analysis Requirements**: The following linters/tools MUST pass:
   - Code formatter (e.g., `black` for Python, `prettier` for JavaScript)
   - Linter for complexity metrics (e.g., `flake8` with McCabe complexity plugin)
   - Type checker if language supports it (e.g., `mypy` for Python, TypeScript compiler)

4. **Breaking Change Protocol**: Changes violating established patterns MUST:
   - Document the specific constitutional violation
   - Provide technical justification for the deviation
   - Propose either an amendment to the constitution or a refactoring to restore compliance

5. **Onboarding Documentation**: New contributors MUST be directed to this constitution as their first reading material. The README MUST link to this document prominently.

---

## Governance

**Authority**: This constitution supersedes all other coding practices, conventions, or preferences. When conflicts arise between this document and external style guides, this document prevails.

**Amendment Procedure**:

1. Proposed amendments MUST be submitted as pull requests modifying this file
2. Amendments require:
   - Rationale explaining why current rule is insufficient
   - Impact analysis on existing codebase
   - Migration plan if amendment affects existing code
3. Approval requires sign-off from at least one Distinguished Engineer or project maintainer
4. Upon approval, version is incremented (see Versioning Policy below)

**Versioning Policy**:

- **MAJOR** (X.0.0): Backward-incompatible changes (e.g., removing a principle, changing core security requirements)
- **MINOR** (x.Y.0): New principles added, existing principles materially expanded
- **PATCH** (x.y.Z): Clarifications, wording improvements, typo fixes, non-semantic refinements

**Compliance Review**: Every feature implementation MUST include a "Constitution Check" section in `plan.md` documenting:

- Which articles apply to this feature
- Any areas of uncertainty requiring clarification
- Complexity justifications if rules are bent (rare, requires strong rationale)

**Living Document**: This constitution is maintained in `.specify/memory/constitution.md`. Runtime development guidance for AI agents is derived from this document but stored separately in agent-specific context files.

---

**Version**: 1.1.0 | **Ratified**: 2025-11-29 | **Last Amended**: 2025-11-29
