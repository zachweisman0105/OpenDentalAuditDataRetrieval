# Implementation Plan: OpenDental Audit Data Retrieval CLI

**Branch**: `001-audit-data-cli` | **Date**: 2025-11-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-audit-data-cli/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

CLI tool that accepts PatNum (Patient Number) and AptNum (Appointment Number) as inputs, retrieves audit data from multiple OpenDental API endpoints (patient details, appointments, treatment history, billing, insurance claims, clinical notes), and outputs consolidated JSON. Implements HIPAA-compliant security with OS keyring credential storage, PHI sanitization in logs, optional PHI redaction in output, defensive API integration with retry/timeout/circuit breaker patterns, and 100% mocked testing. Built with Python using Pydantic for data validation, HTTPX for async HTTP with robust error handling, and Keyring for secure credential management.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**:
- **Pydantic 2.5+**: Data validation, schema definition, JSON serialization for all entities and API responses
- **HTTPX 0.25+**: Async HTTP client with timeout/retry support, connection pooling, TLS 1.2+ enforcement
- **Keyring 24.3+**: Cross-platform OS credential storage (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **Click 8.1+**: CLI framework for command parsing, argument validation, subcommands
- **Rich 13.7+**: Terminal formatting for user-friendly output, progress indicators, error display
- **Structlog 23.2+**: Structured logging with PHI sanitization filters
- **pytest 7.4+**: Test framework with fixtures, parametrization, coverage reporting
- **pytest-asyncio 0.21+**: Async test support for HTTPX client testing
- **respx 0.20+**: HTTPX mock library for testing API interactions
- **Faker 20.1+**: Synthetic PHI generation for test fixtures

**Storage**: File system only (JSON output files, audit logs with 600 permissions). No database.

**Testing**: pytest with 100% mock coverage (no live API calls per Article IV). Test structure: tests/unit/, tests/integration/, tests/contract/, tests/fixtures/

**Target Platform**: Cross-platform CLI (Windows 10+, macOS 10.15+, Linux with keyring support)

**Project Type**: Single project (CLI application)

**Performance Goals**: 
- <60s total retrieval time for patient-appointment data (6 endpoints, sequential with retry)
- <10s test suite execution (offline, fully mocked)
- <100MB memory footprint during execution
- Handle up to 50MB total API response data

**Constraints**: 
- HIPAA compliance: Zero PHI in logs, encrypted keyring storage, TLS 1.2+ only
- Offline testability: No network dependencies in test suite
- Cross-platform keyring: Must work on Windows/macOS/Linux or fail gracefully
- Function size: 30 lines max (Article I)
- Cyclomatic complexity: 10 max per function (Article I)

**Scale/Scope**: 
- Single-user CLI tool (no concurrent user management)
- ~1500-2000 LOC for core functionality
- 6-8 API endpoints per retrieval
- Single OpenDental environment per credential set

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Article I: Cognitive Load & Readability

| Law | Compliance Status | Implementation Plan |
|-----|-------------------|---------------------|
| Function Atomicity (30 lines) | ✅ PASS | Click decorators + Pydantic validators enforce small functions. Complex operations decomposed (e.g., `fetch_endpoint()`, `validate_response()`, `sanitize_field()` as separate functions) |
| Anti-Monolith (no logic in main) | ✅ PASS | `main()` uses Click for argument parsing, delegates to orchestration functions. Business logic in domain modules |
| Naming Precision | ✅ PASS | Module structure: `credential_manager`, `api_client`, `phi_sanitizer`, `output_formatter`, `audit_logger`. No `utils` or `helpers` |
| Single Responsibility | ✅ PASS | Each module has one cohesive purpose aligned with functional requirements |
| Dependency Inversion | ✅ PASS | HTTPX client injected via constructor, Keyring accessed through credential_manager abstraction |
| Cyclomatic Complexity (≤10) | ✅ PASS | Pytest + radon for complexity measurement in CI. Conditional logic decomposed into predicate functions |

### Article II: HIPAA-Compliant Security Posture

| Law | Compliance Status | Implementation Plan |
|-----|-------------------|---------------------|
| Credential Isolation | ✅ PASS | Keyring library for OS-native storage. Environment variable fallback with warning. No CLI args for credentials |
| Encryption-at-Rest | ✅ PASS | Keyring handles encryption transparently. Output files created with mode 0o600. Audit logs restricted permissions |
| Logging Sanitization | ✅ PASS | Structlog with custom `PHISanitizerProcessor` filters PatNum, names, DOBs, dates, SSNs from all log output |
| Error Handling Protocol | ✅ PASS | Generic user messages via Rich. Detailed traces to audit log (non-PHI). HTTP errors sanitized |
| Output Redaction Rule | ✅ PASS | `--redact-phi` flag triggers `PHIRedactor` class to replace sensitive fields with `[REDACTED]` |
| Memory Management | ✅ PASS | Python GC handles cleanup. Explicit `del` for large response objects. No persistent caching of PHI |
| Data Destruction | ⚠️ CLARIFICATION | Python doesn't support secure memory zeroing. Document limitation in security notes. Rely on GC + no swap encryption recommendation |
| Audit Trail | ✅ PASS | Every API call logged to `audit.log` with timestamp (UTC), endpoint, status, duration. No PHI |
| Transmission Security | ✅ PASS | HTTPX configured with `verify=True` (TLS 1.2+), no certificate bypass even in dev |
| Keyring Integration | ✅ PASS | Service name: `opendental-audit-cli`. `config set-credentials` subcommand. Fail if keyring unavailable without env vars |

### Article III: Defensive API Integration

| Law | Compliance Status | Implementation Plan |
|-----|-------------------|---------------------|
| Timeout Discipline | ✅ PASS | HTTPX client: `timeout=httpx.Timeout(10.0, read=30.0, write=10.0, pool=10.0)`. Total request timeout 45s via asyncio |
| Retry Policy Standard | ✅ PASS | Custom retry decorator with exponential backoff (1s, 2s, 4s), jitter (±20%), max 3 attempts. Retry on network errors + 5xx only |
| Rate Limit Handling | ✅ PASS | Detect HTTP 429, parse `Retry-After` header, wait + retry. User feedback via Rich progress |
| Partial Failure Isolation | ✅ PASS | `asyncio.gather(return_exceptions=True)` for concurrent endpoint fetches. Success/failure segregation in output JSON |
| Circuit Breaker Pattern | ✅ PASS | Simple circuit breaker class: 5 failures → 60s open state → half-open probe. Per-endpoint state tracking |
| Response Validation | ✅ PASS | Pydantic models validate all API responses. Missing required fields raise ValidationError treated as endpoint failure |
| Idempotency Awareness | ✅ PASS | All operations are GET requests (read-only). Safe to retry |

### Article IV: Developer Experience & Testability

| Law | Compliance Status | Implementation Plan |
|-----|-------------------|---------------------|
| Absolute API Call Prohibition | ✅ PASS | pytest with `respx` to mock all HTTPX requests. CI network monitoring (optional: pytest-socket to block network) |
| Mock Implementation Strategy | ✅ PASS | `tests/fixtures/` with JSON files per endpoint. `load_fixture()` helper. Success + error scenarios |
| Dependency Injection | ✅ PASS | API client injected into all functions. Test doubles use `respx.MockRouter` |
| Test Organization | ✅ PASS | Directory structure: `tests/unit/`, `tests/integration/`, `tests/contract/`, `tests/fixtures/` |
| Fast Feedback Loop | ✅ PASS | Target <10s for full suite. Async tests parallelized. No I/O except fixture loading |
| Maximum Coverage Target | ✅ PASS | pytest-cov with 90% general, 100% for `credential_manager`, `phi_sanitizer`, `audit_logger` modules |
| Fake Data Generation | ✅ PASS | Faker library for synthetic PHI in fixtures. Unicode edge cases included |
| Error Scenario Coverage | ✅ PASS | Every test module has `test_*_error_*` functions for timeout, 404, 500, 503, malformed JSON |
| Documentation Through Tests | ✅ PASS | `tests/integration/test_golden_path.py` as executable spec |
| Test Isolation Enforcement | ✅ PASS | Pytest fixtures for setup/teardown. No global state. Mock file system with `tmp_path` |
| Local Development Iteration | ✅ PASS | Mock mode flag for CLI to run against fixtures without credentials |

### Pre-Research Gate Results

**Status**: ✅ **PASSED** with 1 clarification

**Violations**: None

**Clarifications**:
1. **Article II, Law 7 (Data Destruction)**: Python's automatic garbage collection doesn't support explicit memory zeroing. Recommendation: Document this limitation and advise users to enable system-level protections (encrypted swap, no hibernation with PHI in memory). This is acceptable for scripting language constraints.

**Justifications**: N/A - No violations requiring justification

**Action**: Proceed to Phase 0 (Research)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── opendental_cli/
│   ├── __init__.py
│   ├── __main__.py              # Entry point (python -m opendental_cli)
│   ├── cli.py                   # Click commands (main, config)
│   ├── models/                  # Pydantic data models
│   │   ├── __init__.py
│   │   ├── request.py           # AuditDataRequest
│   │   ├── credential.py        # APICredential
│   │   ├── response.py          # EndpointResponse, ConsolidatedAuditData
│   │   ├── audit_log.py         # AuditLogEntry
│   │   └── opendental/          # OpenDental API response schemas
│   │       ├── __init__.py
│   │       ├── patient.py
│   │       ├── appointment.py
│   │       ├── treatment.py
│   │       ├── billing.py
│   │       ├── insurance.py
│   │       └── clinical_notes.py
│   ├── api_client.py            # HTTPX-based API client (timeout, retry, circuit breaker)
│   ├── credential_manager.py    # Keyring integration, env variable fallback
│   ├── phi_sanitizer.py         # Structlog processor for PHI removal
│   ├── phi_redactor.py          # Output redaction for --redact-phi flag
│   ├── output_formatter.py      # JSON consolidation and file writing
│   ├── audit_logger.py          # Audit trail logging configuration
│   └── circuit_breaker.py       # Circuit breaker pattern implementation
│
├── pyproject.toml               # Poetry/setuptools config, dependencies
├── README.md                    # Installation, usage, security notes
├── .env.template                # Example for env variable fallback
└── .gitignore

tests/
├── __init__.py
├── conftest.py                  # Shared pytest fixtures
├── fixtures/                    # JSON response fixtures
│   ├── patient_12345.json
│   ├── patient_404.json
│   ├── appointment_67890.json
│   ├── appointment_503.json
│   ├── treatment_success.json
│   ├── billing_timeout.json
│   ├── insurance_malformed.json
│   └── clinical_notes_success.json
├── unit/
│   ├── test_credential_manager.py
│   ├── test_phi_sanitizer.py
│   ├── test_phi_redactor.py
│   ├── test_output_formatter.py
│   ├── test_audit_logger.py
│   ├── test_circuit_breaker.py
│   └── test_models.py
├── integration/
│   ├── test_golden_path.py      # End-to-end success scenario
│   ├── test_partial_failure.py  # Mixed success/failure
│   └── test_credential_flow.py  # Config subcommand
└── contract/
    ├── test_api_client_timeout.py
    ├── test_api_client_retry.py
    ├── test_api_client_rate_limit.py
    └── test_response_validation.py
```

**Structure Decision**: Single project layout (Option 1) selected. This is a CLI application with no web/mobile components. Flat module structure under `src/opendental_cli/` follows Python packaging best practices. Models directory separates Pydantic schemas by domain (internal request/response models vs OpenDental API schemas). Tests mirror source structure with comprehensive fixture library.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: No violations - this section intentionally left empty.

All constitution requirements met. See Constitution Check section above for compliance details.

---

## Post-Design Constitution Check

*Executed after Phase 1 design completion (research.md, data-model.md, contracts/, quickstart.md)*

### Article I: Cognitive Load & Readability

| Design Artifact | Compliance Finding |
|-----------------|-------------------|
| **data-model.md** | ✅ **PASS** - 11 Pydantic models each with single responsibility. Longest model (`ConsolidatedAuditData`) has 15 lines. `redact_phi_fields()` methods are 5-8 lines each. Validation logic in Pydantic validators (<10 lines per validator) |
| **contracts/opendental-api.md** | ✅ **PASS** - 6 distinct endpoints with clear separation of concerns. Error handling patterns defined per endpoint, not monolithic. Each endpoint contract fits in 40-50 lines including examples |
| **quickstart.md test scenarios** | ✅ **PASS** - Test examples follow function decomposition pattern. Example test functions are 15-25 lines. Mock setup, execution, and assertions clearly separated |

**Verdict**: Article I compliance maintained through design phase. No function size violations anticipated in implementation.

---

### Article II: HIPAA-Compliant Security Posture

| Design Artifact | Compliance Finding |
|-----------------|-------------------|
| **data-model.md** | ✅ **PASS** - `APICredential` uses Pydantic `SecretStr` for api_key field. All models include `redact_phi_fields()` method returning sanitized copy. PHI fields identified: FName, LName, Address, Phone, Email, SSN, Birthdate, ProcDescript, ToothNum, NoteText |
| **contracts/opendental-api.md** | ✅ **PASS** - All endpoints use Bearer token auth (no credential leakage). TLS 1.2+ enforcement specified. Security notes section mandates no raw response logging. Timeout specs prevent indefinite connection hangs |
| **quickstart.md** | ✅ **PASS** - Scenario 10 validates PHI sanitization in logs. Credential setup workflow uses keyring (Scenario 6). Output file permissions set to 600 (Scenario "Save to File"). Mock mode doesn't bypass credential checks in production |

**Verdict**: Article II compliance validated. Design enforces encryption, sanitization, and audit trail requirements. Memory zeroing limitation remains documented as Python constraint.

---

### Article III: Defensive API Integration

| Design Artifact | Compliance Finding |
|-----------------|-------------------|
| **contracts/opendental-api.md** | ✅ **PASS** - Timeout specifications explicit per endpoint: 10s connect, 30s read, 45s total. Retry logic defined: 3 attempts, exponential backoff (1s/2s/4s) with ±20% jitter. Rate limiting documented: 429 handling with Retry-After header respect. Error responses comprehensive (400/401/403/404/429/500/503) |
| **quickstart.md test scenarios** | ✅ **PASS** - Scenario 2 validates partial failure isolation (5 succeed, 1 fails). Scenario 7 tests rate limit handling. Scenario 8 covers circuit breaker behavior. Scenario 3 tests complete timeout failure with graceful degradation. Scenario 9 validates Pydantic response validation |
| **data-model.md** | ✅ **PASS** - Pydantic models enforce required field validation. `EndpointResponse` discriminates success/failure. `ConsolidatedAuditData` segregates successful responses from failures. No silent data corruption possible |

**Verdict**: Article III compliance confirmed. Defensive patterns (timeout, retry, circuit breaker, validation) embedded in design. Partial failure handling explicit in data models.

---

### Article IV: Developer Experience & Testability

| Design Artifact | Compliance Finding |
|-----------------|-------------------|
| **quickstart.md** | ✅ **PASS** - 10 test scenarios defined with explicit fixture references. Mock mode for local development (no API calls). Fixture naming convention documented ({endpoint}_success.json, {endpoint}_404.json). All scenarios use respx for HTTPX mocking. Performance target <10s test suite confirmed |
| **contracts/opendental-api.md** | ✅ **PASS** - Testing section specifies fixture structure. Each endpoint has success + error fixtures. Response schemas allow Pydantic-based test data generation. No live API dependency in contract tests |
| **data-model.md** | ✅ **PASS** - Pydantic models support dependency injection (no global state). `model_validate()` and `model_validate_json()` enable test data creation from fixtures. All models hashable and comparable (equality checks in assertions) |

**Verdict**: Article IV compliance sustained. Design prioritizes testability with comprehensive fixture strategy, mock patterns, and no live API dependencies. Coverage targets achievable with current design.

---

### Post-Design Gate Results

**Status**: ✅ **PASSED**

**New Violations**: None

**Design Improvements Identified**:
1. ✅ **Adopted**: Pydantic `SecretStr` for API key (better than plain string)
2. ✅ **Adopted**: Explicit timeout values per endpoint (not just blanket 45s)
3. ✅ **Adopted**: Fixture naming convention standardization across test scenarios

**Clarifications Resolved**:
- Confirmed Python memory zeroing limitation remains acceptable (system-level encryption recommended in security notes)

**Action**: Proceed to Phase 2 (`/speckit.tasks`) to generate implementation task breakdown

---

## Phase Completion Summary

### Phase 0: Research & Discovery ✅ COMPLETE

**Output**: `research.md`

**Completed**:
- 7 research questions resolved
- Technology choices validated (Python 3.11+, Pydantic, HTTPX, Keyring, Click)
- OpenDental API authentication pattern confirmed (Bearer token)
- Best practices documented for HTTPX retry, Structlog PHI sanitization, circuit breaker implementation
- Alternatives considered and documented (Typer vs Click, tenacity vs custom retry, respx vs httpretty)

**Key Decisions**:
- Click framework chosen for CLI (mature, stable, explicit over magic)
- tenacity library for retry logic (battle-tested exponential backoff)
- Custom circuit breaker (<30 lines, no heavy dependency)
- Pydantic model inheritance for OpenDental response schemas

---

### Phase 1: Design & Contracts ✅ COMPLETE

**Outputs**:
1. `data-model.md` - 11 Pydantic models with validation rules
2. `contracts/opendental-api.md` - 6 API endpoint specifications
3. `quickstart.md` - 10 test scenarios with fixture examples
4. `.github/agents/copilot-instructions.md` - Agent context updated with Python 3.11+ tech stack

**Completed**:
- ✅ Data models defined for all entities (request, response, credentials, audit logs)
- ✅ OpenDental API response schemas modeled (6 endpoints)
- ✅ PHI redaction methods implemented in all models
- ✅ API contracts documented with request/response examples, error codes, timeout specs
- ✅ Test scenarios covering golden path, partial failures, error cases, PHI sanitization
- ✅ Fixture naming conventions established
- ✅ Mock mode strategy defined for local development
- ✅ Agent context file updated (GitHub Copilot)

**Constitution Re-Check**: All 4 Articles remain compliant post-design

---

### Artifacts Generated

```
specs/001-audit-data-cli/
├── spec.md                          # ✅ Feature specification (from /speckit.specify)
├── checklists/requirements.md       # ✅ Validation checklist (from /speckit.checklist)
├── plan.md                          # ✅ This file (from /speckit.plan)
├── research.md                      # ✅ Phase 0 output (7 questions resolved)
├── data-model.md                    # ✅ Phase 1 output (11 Pydantic models)
├── contracts/opendental-api.md      # ✅ Phase 1 output (6 API endpoints)
└── quickstart.md                    # ✅ Phase 1 output (10 test scenarios)
```

**Additional Files**:
- `.github/agents/copilot-instructions.md` - Agent context for GitHub Copilot
- `.specify/memory/constitution.md` - v1.1.0 (4 Articles, 40+ laws)

---

### Next Steps

1. **Run `/speckit.tasks`** to generate `tasks.md` with implementation breakdown
2. **Review task priorities** against user stories (P1: Basic Retrieval, P2: PHI Redaction & Credentials)
3. **Begin implementation** with TDD approach using quickstart.md scenarios
4. **Validate at each milestone** against constitution compliance matrix

---

### Branch & Status

**Git Branch**: `001-audit-data-cli`  
**Plan Status**: Phase 0-1 COMPLETE (Research & Design)  
**Constitution Compliance**: ✅ PASS (Pre-Research & Post-Design checks)  
**Ready for Phase 2**: YES - Execute `/speckit.tasks` to proceed

---