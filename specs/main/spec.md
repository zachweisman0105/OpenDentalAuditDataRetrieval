# Feature Specification: Fix OpenDental FHIR Authorization Format

**Priority**: P0 (Critical - Blocking all API calls)  
**Date**: 2025-12-02  
**Status**: Planning

## Problem Statement

The CLI is experiencing 401 Unauthorized errors on all OpenDental API endpoints despite having correct credentials. Investigation reveals the authorization header format is incorrect.

**Current Implementation** (INCORRECT):
```http
DeveloperKey: {developer_key}
CustomerKey: {customer_key}
```

**Required Format** (CORRECT):
```http
Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}
```

The API uses OpenDental FHIR authentication which requires credentials to be combined into a single `Authorization` header with the `ODFHIR` prefix, not sent as separate custom headers.

## User Stories

### US1: As a developer, I need the API client to use correct authorization format so that API calls succeed (Priority: P0)

**Acceptance Criteria**:
1. Authorization header uses format: `Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}`
2. No separate `DeveloperKey` or `CustomerKey` headers are sent
3. All 6 endpoints (procedurelogs, allergies, medicationpats, diseases, patientnotes, vital_signs) return 200 OK instead of 401
4. Existing credential storage and retrieval logic remains unchanged (only header construction changes)

**Technical Requirements**:
- Modify `get_auth_header()` in `credential.py` to return single `Authorization` header
- Update API contract documentation to reflect correct format
- Verify field names remain `developer_key` and `customer_key` in credential model (but customer_key represents DeveloperPortalKey)
- Update tests to verify new header format

### US2: As a user, I need clear credential prompts so I understand which keys to enter (Priority: P1)

**Acceptance Criteria**:
1. CLI prompts for "Developer Key" (first part of ODFHIR auth)
2. CLI prompts for "Developer Portal Key" (second part of ODFHIR auth, currently called "Customer Key")
3. Documentation clearly explains the ODFHIR format and where to obtain keys
4. Error messages distinguish between auth format errors and invalid credentials

**Technical Requirements**:
- Update `cli.py` to change prompt text from "Customer Key" to "Developer Portal Key"
- Add inline help text explaining ODFHIR format
- Update README with credential configuration section

### US3: As a developer, I need updated tests to validate the authorization format (Priority: P1)

**Acceptance Criteria**:
1. Unit tests verify `get_auth_header()` returns single `Authorization` header with ODFHIR prefix
2. Contract tests verify API client sends Authorization header (not DeveloperKey/CustomerKey)
3. Integration tests pass with mocked API using correct header format
4. No tests make real API calls (Constitution Article IV compliance)

## Technical Approach

### Phase 0: Research (Complete)
- ✅ Identified authorization format discrepancy
- ✅ Confirmed correct format: `Authorization: ODFHIR {key1}/{key2}`
- ✅ Verified credential storage works correctly (issue is only in header construction)

### Phase 1: Fix Authorization Header Construction
1. Update `src/opendental_cli/models/credential.py`:
   - Change `get_auth_header()` to return: `{"Authorization": f"ODFHIR {developer_key}/{customer_key}"}`
   - Add docstring explaining ODFHIR format

2. Update `specs/001-audit-data-cli/contracts/opendental-api.md`:
   - Replace custom header documentation with Authorization header format
   - Add examples showing `Authorization: ODFHIR key1/key2`

3. Update `src/opendental_cli/cli.py`:
   - Change prompt from "Customer Key" to "Developer Portal Key"
   - Add help text explaining ODFHIR format

### Phase 2: Update Tests
1. Update `tests/unit/test_models.py`:
   - Verify `get_auth_header()` returns single Authorization header
   - Verify format: `ODFHIR {key1}/{key2}`

2. Update contract tests in `tests/contract/`:
   - Verify API client sends Authorization header
   - Remove checks for DeveloperKey/CustomerKey headers

3. Update integration tests in `tests/integration/`:
   - Update mocked responses to accept Authorization header
   - Verify error handling for 401 responses

### Phase 3: Documentation
1. Update `README.md`:
   - Add "Authentication" section explaining ODFHIR format
   - Document credential configuration: `opendental-cli config set-credentials`
   - Explain where to obtain Developer Key and Developer Portal Key

2. Update `SECURITY.md`:
   - Document Authorization header format for security review
   - Confirm credentials never logged or displayed

## Out of Scope

- Changing credential storage mechanism (keyring implementation stays the same)
- Adding support for alternative authentication methods
- Modifying API endpoint paths or HTTP methods

## Risks & Mitigation

**Risk**: Existing stored credentials may need re-entry after field rename
- **Mitigation**: Credentials remain in same keyring fields (`developer_key`, `customer_key`), only prompt text changes

**Risk**: Tests may fail if mocked API doesn't accept new header format
- **Mitigation**: Update all test fixtures and mocks before running full test suite

## Success Metrics

- All 6 API endpoints return 200 OK with valid credentials
- Test suite passes with 90%+ coverage
- Zero PHI logged in error messages or debug output
- Documentation clearly explains ODFHIR authentication

## Dependencies

- No new external dependencies
- No database changes
- No infrastructure changes

## Timeline Estimate

- Phase 0 (Research): ✅ Complete
- Phase 1 (Implementation): 30 minutes
- Phase 2 (Testing): 30 minutes
- Phase 3 (Documentation): 15 minutes
- **Total**: ~1.25 hours
