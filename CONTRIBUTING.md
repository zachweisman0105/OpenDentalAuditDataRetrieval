# Contributing to OpenDental Audit CLI

Thank you for your interest in contributing! This guide will help you set up your development environment and understand the project's coding standards.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- OS with keyring support (Windows 10+, macOS 10.15+, or Linux with GNOME Keyring/KWallet)

### Local Development

```bash
# Clone repository
git clone https://github.com/opendental/audit-cli.git
cd OpenDentalAuditDataRetrieval

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Verify installation
opendental-cli --help
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opendental_cli --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_api_client.py -v

# Run tests matching pattern
pytest -k "test_credential" -v
```

### Test Requirements

- **100% mocked**: No tests should make actual API calls
- **90%+ coverage**: Overall code coverage target
- **100% coverage**: Security-critical modules (credential_manager, phi_sanitizer, audit_logger)
- **Offline execution**: All tests must run without network access

## Code Quality Standards

### Constitution Compliance

This project follows a strict constitution defined in `.specify/memory/constitution.md`:

#### Article I: Code Quality & Maintainability

- ✅ Functions ≤30 lines
- ✅ Cyclomatic complexity ≤10
- ✅ Descriptive names (no abbreviations except PatNum, AptNum)
- ✅ Comprehensive docstrings with Args, Returns, Raises

#### Article II: HIPAA Security

- ✅ No PHI in logs, errors, or console output
- ✅ Audit trail with UTC timestamps, no PHI
- ✅ File permissions 0o600 for output files
- ✅ OS keyring with AES-256-GCM encryption

#### Article III: Defensive API Programming

- ✅ Timeout enforcement (45s total, 10s connect, 30s read)
- ✅ Retry with exponential backoff (3 attempts: 1s, 2s, 4s ±20% jitter)
- ✅ Circuit breaker (5 failures → 60s cooldown)
- ✅ Rate limit handling (429 with Retry-After header)
- ✅ TLS 1.2+ with certificate validation

#### Article IV: Test Coverage

- ✅ 90%+ overall coverage
- ✅ 100% mocked tests (no live API calls)
- ✅ Offline test execution

### Code Quality Checks

```bash
# Check cyclomatic complexity
radon cc src/ --total-average

# Check lines per function
radon raw src/

# Run type checking (if using mypy)
mypy src/

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/
```

## Contribution Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following constitution guidelines
- Add tests (unit + integration)
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run tests
pytest

# Check coverage
pytest --cov=opendental_cli --cov-report=term

# Verify constitution compliance
radon cc src/ --total-average
radon raw src/ | grep -A 1 "LOC:"
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: Add feature description"
```

**Commit Message Format**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `test:` Test addition/modification
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] All tests pass (`pytest`)
- [ ] Code coverage meets 90%+ target
- [ ] No PHI leakage in new code (check logs, errors, output)
- [ ] Functions are ≤30 lines
- [ ] Cyclomatic complexity ≤10
- [ ] All API calls use timeout, retry, circuit breaker
- [ ] New tests are fully mocked (no live API calls)
- [ ] Documentation updated (if applicable)
- [ ] SECURITY.md updated (if security-relevant changes)
- [ ] No new security vulnerabilities (`safety check`)

## Common Development Tasks

### Adding a New API Endpoint

1. **Define Response Model** (`src/opendental_cli/models/opendental/`)
   ```python
   from pydantic import BaseModel, Field
   
   class NewEndpointResponse(BaseModel):
       """Response from new endpoint."""
       field1: str = Field(description="Description")
       # ... other fields
   ```

2. **Add Fetch Method** (`src/opendental_cli/api_client.py`)
   ```python
   @retry(...)
   async def fetch_new_endpoint(self, id: int) -> EndpointResponse:
       """Fetch data from new endpoint."""
       # Implementation with timeout, retry, circuit breaker
   ```

3. **Update Orchestrator** (`src/opendental_cli/orchestrator.py`)
   - Add new endpoint to concurrent fetch list
   - Handle response in consolidation logic

4. **Write Tests**
   - Contract test (golden path)
   - Unit tests (error scenarios)
   - Integration test (full CLI workflow)

5. **Update Documentation**
   - README.md usage examples
   - SECURITY.md if PHI is involved

### Adding PHI Fields

If adding new PHI field types:

1. **Update PHI Sanitizer** (`src/opendental_cli/phi_sanitizer.py`)
   ```python
   PHI_PATTERNS = {
       "new_field": re.compile(r"pattern"),
       # ... other patterns
   }
   ```

2. **Update PHI Redactor** (`src/opendental_cli/phi_redactor.py`)
   ```python
   PHI_FIELDS = {
       "new_field_name",
       # ... other fields
   }
   ```

3. **Add Tests**
   - Unit test for sanitizer pattern
   - Unit test for redactor field
   - Integration test with --redact-phi flag

4. **Update SECURITY.md**
   - Document new PHI field type
   - Update field count in documentation

## Reporting Issues

### Security Vulnerabilities

**DO NOT** open public issues for security vulnerabilities.

Email: security@opendental.example.com

### Bug Reports

Include:
- Python version
- OS and version
- Full error message and traceback
- Steps to reproduce
- Expected vs actual behavior

### Feature Requests

Include:
- Use case description
- Expected behavior
- Why existing features don't meet need
- Willingness to implement (if any)

## Code Review Process

1. **Automated Checks**: CI runs tests, coverage, linting
2. **Manual Review**: Maintainer reviews code quality, security, design
3. **Feedback**: Address review comments
4. **Approval**: Maintainer approves PR
5. **Merge**: Squash and merge to main branch

## Development Best Practices

### Testing

- **Test-Driven Development**: Write tests before implementation (preferred)
- **Coverage Focus**: Aim for 100% coverage on new code
- **Mock Everything**: Never make actual API calls in tests
- **Test Edge Cases**: Invalid inputs, timeouts, network errors, etc.

### Security

- **Never Log PHI**: Use PHISanitizerProcessor for all logging
- **Validate Inputs**: Check PatNum/AptNum are positive integers
- **Secure Defaults**: File permissions 0o600, TLS validation enabled
- **Credential Hygiene**: Never commit API keys, use keyring only

### Documentation

- **Docstrings**: All public functions/classes must have docstrings
- **Type Hints**: Use Python type hints for function signatures
- **Comments**: Explain "why", not "what" (code should be self-explanatory)
- **README**: Update usage examples when adding features

### Performance

- **Async Operations**: Use asyncio for concurrent API calls
- **Resource Limits**: Document max response sizes (50MB)
- **Timeout Enforcement**: Always use timeouts for network operations
- **Memory Efficiency**: Stream large responses if possible

## Questions?

- **Documentation**: Check README.md and SECURITY.md first
- **Issues**: Search existing issues on GitHub
- **Discussion**: Open a GitHub Discussion for general questions
- **Email**: support@opendental.example.com for urgent matters

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for contributing to OpenDental Audit CLI! 🎉
