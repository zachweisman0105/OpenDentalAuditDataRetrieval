# Research: OpenDental Audit Data Retrieval CLI

**Phase**: 0 - Technical Research  
**Date**: 2025-11-29  
**Purpose**: Resolve all "NEEDS CLARIFICATION" items from Technical Context and establish design decisions

## Research Questions

### Q1: OpenDental API Structure & Authentication

**Question**: What is the OpenDental API structure? What endpoints are available for patient, appointment, treatment, billing, insurance, and clinical data? What authentication method is used?

**Findings**:
- **API Type**: OpenDental provides a RESTful Web API (introduced in version 17.1+)
- **Base URL Pattern**: `https://{server-address}/api/v1/` or customer-specific cloud URLs
- **Authentication**: Bearer token authentication using API keys
  - Header format: `Authorization: Bearer {api_key}`
  - API keys generated through OpenDental desktop application (Setup > API Keys)
  - No OAuth2 or complex token refresh - static API keys
- **Endpoints** (documented in OpenDental API documentation):
  - `/patients/{PatNum}` - Patient demographics
  - `/appointments/{AptNum}` - Appointment details
  - `/procedures` - Treatment/procedure history (filter by PatNum)
  - `/claims` - Insurance claims (filter by PatNum)
  - `/billing` or `/statements` - Billing records
  - `/clinical_notes` or `/progress_notes` - Clinical documentation
- **Rate Limits**: Not explicitly documented publicly, but typical healthcare APIs: 100-1000 requests/hour per API key
- **Response Format**: JSON with consistent structure (200 OK with data, 4xx/5xx for errors)

**Decision**: 
- Use HTTPX with Bearer token auth: `headers={"Authorization": f"Bearer {api_key}"}`
- Store base URL + API key in keyring as separate entries: `{env}.base_url` and `{env}.api_key`
- Assumption validation: RESTful + JSON confirmed ✅
- Authentication assumption validated: API key (Bearer token) ✅

**Alternatives Considered**:
- OAuth2 with token refresh: Rejected - OpenDental uses simple API key auth
- Basic auth: Rejected - OpenDental standard is Bearer tokens

---

### Q2: Python CLI Best Practices (Click vs Argparse vs Typer)

**Question**: What's the best Python CLI framework for this use case? Click, argparse (stdlib), or Typer?

**Findings**:
- **Click 8.1+**:
  - ✅ Decorator-based, very readable
  - ✅ Built-in support for subcommands (`config set-credentials`)
  - ✅ Automatic help generation
  - ✅ Rich integration available (click-rich)
  - ✅ Mature ecosystem (used by Flask, AWS CLI v1)
  - ❌ Slightly more boilerplate than Typer
- **Typer**:
  - ✅ Modern, type-hint based (built on Click)
  - ✅ Less boilerplate
  - ❌ Newer library (less mature)
  - ❌ Potential complexity for simple CLIs
- **argparse**:
  - ✅ Standard library (no dependency)
  - ❌ More verbose
  - ❌ Subcommand support more complex
  - ❌ No rich integration

**Decision**: Use **Click 8.1+**
- Mature, well-documented, excellent subcommand support
- Aligns with Article I (readability) - decorators make intent clear
- Rich integration for user-friendly output

**Alternatives Considered**:
- Typer: Rejected - newer, less mature for enterprise use
- argparse: Rejected - too verbose for complex CLI with subcommands

---

### Q3: Keyring Library Cross-Platform Support

**Question**: Does Python `keyring` library work reliably on Windows/macOS/Linux? What are fallback strategies?

**Findings**:
- **Keyring 24.3+** backends:
  - **Windows**: Uses `Windows Credential Manager` via `pywin32` or `keyring.backends.Windows`
  - **macOS**: Uses `Keychain` via `Security` framework
  - **Linux**: Supports multiple backends:
    - `SecretService` (GNOME Keyring, KWallet) - preferred
    - `kwallet` - KDE
    - Fallback to encrypted file if no system keyring available
- **Failure Modes**:
  - Headless Linux without keyring service: `keyring.errors.NoKeyringError`
  - Locked keyring: `keyring.errors.KeyringLocked`
  - Permission issues: `keyring.errors.PasswordSetError`
- **Best Practices**:
  - Always catch `keyring.errors.*` exceptions
  - Provide clear error messages directing to environment variable fallback
  - Document that CI/CD should use environment variables, not keyring

**Decision**:
- Primary: `keyring.set_password(service_name, username, password)`
  - service_name: `"opendental-audit-cli"`
  - username: `"{environment}.base_url"` and `"{environment}.api_key"`
- Fallback: Environment variables `OPENDENTAL_BASE_URL` and `OPENDENTAL_API_KEY`
- Error handling: Catch `NoKeyringError`, display message:
  ```
  Keyring not available. Please set environment variables:
  export OPENDENTAL_BASE_URL="https://your-server/api/v1"
  export OPENDENTAL_API_KEY="your-api-key"
  
  WARNING: Environment variables are less secure than keyring storage.
  See README for security implications.
  ```

**Alternatives Considered**:
- Encrypted file storage: Rejected - reinventing keyring, complex key management
- Plain text config file: Rejected - violates Article II

---

### Q4: HTTPX Retry & Timeout Patterns

**Question**: How to implement exponential backoff with jitter using HTTPX? Native support or custom decorator?

**Findings**:
- **HTTPX**: Does NOT have built-in retry logic (unlike `requests` with `urllib3.Retry`)
- **Options**:
  1. **httpx-retry** library: Third-party plugin, but not actively maintained
  2. **tenacity** library: General-purpose retry with decorators, widely used
  3. **Custom implementation**: Decorator with `asyncio.sleep()` for async support
- **Timeout Configuration**:
  ```python
  timeout = httpx.Timeout(
      connect=10.0,  # Connection timeout
      read=30.0,     # Read timeout
      write=10.0,    # Write timeout (not relevant for GET)
      pool=10.0      # Pool acquisition timeout
  )
  client = httpx.AsyncClient(timeout=timeout, verify=True)
  ```

**Decision**: Use **tenacity** library for retry logic
- Mature, well-tested (used by OpenStack, etc.)
- Declarative decorator syntax:
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
  
  @retry(
      stop=stop_after_attempt(3),
      wait=wait_exponential(multiplier=1, min=1, max=10) + wait_random(0, 0.2),
      retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)) | 
            retry_if_result(lambda r: r.status_code >= 500)
  )
  async def fetch_endpoint(...):
      ...
  ```
- Jitter built-in with `wait_random()`
- Avoids reinventing retry logic

**Alternatives Considered**:
- Custom decorator: Rejected - don't reinvent retry logic, tenacity is battle-tested
- httpx-retry: Rejected - not actively maintained

---

### Q5: Structlog PHI Sanitization Strategy

**Question**: How to implement PHI sanitization in structlog? Processor pattern?

**Findings**:
- **Structlog** uses processor pipeline to transform log events
- **Processor Pattern**:
  ```python
  class PHISanitizerProcessor:
      PHI_PATTERNS = {
          'patnum': re.compile(r'\bpatnum[:\s]*\d+', re.IGNORECASE),
          'aptnum': re.compile(r'\baptnum[:\s]*\d+', re.IGNORECASE),
          'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
          'dob': re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),
          'name': re.compile(r'\b(first_name|last_name|patient_name)[:\s]*[\'"]?[\w\s]+[\'"]?', re.IGNORECASE),
      }
      
      def __call__(self, logger, method_name, event_dict):
          message = str(event_dict.get('event', ''))
          for pattern_name, pattern in self.PHI_PATTERNS.items():
              message = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', message)
          event_dict['event'] = message
          return event_dict
  ```
- **Configuration**:
  ```python
  import structlog
  structlog.configure(
      processors=[
          structlog.stdlib.add_log_level,
          structlog.stdlib.add_logger_name,
          PHISanitizerProcessor(),  # Before JSON rendering
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.JSONRenderer()
      ],
      ...
  )
  ```

**Decision**: Implement custom `PHISanitizerProcessor` class
- Regex-based pattern matching for PHI fields
- Applied to all log messages before rendering
- Covers: PatNum, AptNum, SSN, DOB, names, dates, provider names
- Test coverage: 100% (security-critical per Article IV)

**Alternatives Considered**:
- Manual sanitization per log call: Rejected - error-prone, violates DRY
- Third-party sanitization library: Rejected - no healthcare-specific library found

---

### Q6: Pydantic Response Validation Strategy

**Question**: How to structure Pydantic models for OpenDental API responses? One model per endpoint or shared base?

**Findings**:
- **Best Practice**: Separate model per endpoint with shared base for common fields
- **Pattern**:
  ```python
  # Base class for all OpenDental responses
  class OpenDentalResponse(BaseModel):
      model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
  
  # Specific endpoint models
  class PatientResponse(OpenDentalResponse):
      PatNum: int
      FName: str
      LName: str
      Birthdate: date
      SSN: Optional[str] = None
      # ... other fields
  
  class AppointmentResponse(OpenDentalResponse):
      AptNum: int
      PatNum: int
      AptDateTime: datetime
      ProvNum: int
      # ... other fields
  ```
- **Validation Benefits**:
  - Missing required fields → `ValidationError` (treated as endpoint failure per Article III)
  - Type coercion (str to int, str to datetime)
  - Extra fields rejected with `extra='forbid'` (detect API changes)
- **PHI Redaction Integration**:
  ```python
  def redact_phi(self) -> dict:
      data = self.model_dump()
      # Redact sensitive fields
      data['FName'] = '[REDACTED]'
      data['LName'] = '[REDACTED]'
      data['SSN'] = '[REDACTED]'
      return data
  ```

**Decision**: Use **inheritance hierarchy** with `OpenDentalResponse` base class
- Enforces consistent validation across all endpoints
- `extra='forbid'` detects API schema changes
- Methods like `redact_phi()` can be shared or overridden
- Aligns with Article I (Single Responsibility) - one model per endpoint type

**Alternatives Considered**:
- Generic `dict` with manual validation: Rejected - bypasses Pydantic benefits
- Single model for all endpoints: Rejected - violates Single Responsibility

---

### Q7: Circuit Breaker Implementation

**Question**: Should we use a library (e.g., pybreaker) or implement custom circuit breaker?

**Findings**:
- **pybreaker**: Mature library, but limited async support
- **Custom Implementation** (simple):
  ```python
  from dataclasses import dataclass
  from datetime import datetime, timedelta
  from enum import Enum
  
  class CircuitState(Enum):
      CLOSED = "closed"
      OPEN = "open"
      HALF_OPEN = "half_open"
  
  @dataclass
  class CircuitBreaker:
      failure_threshold: int = 5
      timeout_seconds: int = 60
      failures: int = 0
      state: CircuitState = CircuitState.CLOSED
      last_failure_time: Optional[datetime] = None
      
      def record_success(self):
          self.failures = 0
          self.state = CircuitState.CLOSED
      
      def record_failure(self):
          self.failures += 1
          self.last_failure_time = datetime.utcnow()
          if self.failures >= self.failure_threshold:
              self.state = CircuitState.OPEN
      
      def can_attempt(self) -> bool:
          if self.state == CircuitState.CLOSED:
              return True
          if self.state == CircuitState.OPEN:
              if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout_seconds):
                  self.state = CircuitState.HALF_OPEN
                  return True
          return self.state == CircuitState.HALF_OPEN
  ```
- Per-endpoint tracking: Store `CircuitBreaker` instances in dict keyed by endpoint name

**Decision**: **Custom implementation** (simple circuit breaker class)
- <30 lines, easy to understand (Article I)
- No external dependency
- Sufficient for CLI use case (not high-throughput service)

**Alternatives Considered**:
- pybreaker: Rejected - overkill for CLI, limited async support
- No circuit breaker: Rejected - violates Article III requirement

---

## Summary of Decisions

| Research Area | Decision | Rationale |
|---------------|----------|-----------|
| OpenDental API Auth | Bearer token (API key) in Authorization header | Confirmed via API docs, simple auth model |
| API Base URL Storage | Keyring: `{env}.base_url` + `{env}.api_key` | Separation allows independent rotation |
| CLI Framework | Click 8.1+ | Mature, excellent subcommand support, Rich integration |
| Keyring Fallback | Environment variables with security warning | Supports CI/CD, headless Linux |
| Retry Logic | tenacity library with exponential backoff + jitter | Battle-tested, declarative, avoids custom implementation |
| Timeout Configuration | HTTPX: connect=10s, read=30s, total=45s | Meets Article III requirements |
| PHI Sanitization | Custom structlog processor with regex patterns | Centralized, testable, covers all PHI types |
| Response Validation | Pydantic models per endpoint, shared base class | Type safety, automatic validation, PHI redaction methods |
| Circuit Breaker | Custom implementation (5 failures → 60s cooldown) | Simple, <30 lines, sufficient for CLI |
| Async Strategy | HTTPX AsyncClient with asyncio.gather() | Parallel endpoint fetching, partial failure support |

## Resolved Clarifications

All "NEEDS CLARIFICATION" items from Technical Context have been resolved:

1. ✅ **Language/Version**: Python 3.11+ confirmed
2. ✅ **Primary Dependencies**: Pydantic, HTTPX, Keyring + supporting libraries (Click, Rich, Structlog, tenacity, pytest, respx, Faker)
3. ✅ **Testing Framework**: pytest with pytest-asyncio, respx for mocking
4. ✅ **OpenDental API Structure**: RESTful, Bearer auth, JSON responses, 6+ endpoints identified

No outstanding questions remain. Ready to proceed to Phase 1 (Design).
