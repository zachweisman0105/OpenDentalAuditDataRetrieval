# Implementation Plan: API Endpoint Testing & Validation

**Feature**: 003-endpoint-testing  
**Date**: 2025-12-02  
**Estimated Time**: 1.5 hours

## Overview

Create comprehensive tests to verify all API endpoints work correctly with the fixed `dict | list` data type handling. Validate that the fix from specs/002-fix-endpoint-parameters resolves the Pydantic validation errors.

## Prerequisites

- ✅ specs/002-fix-endpoint-parameters completed (EndpointResponse.data accepts dict | list)
- ✅ respx library installed for HTTP mocking
- ✅ pytest and pytest-asyncio configured

---

## Phase 0: Create Test Fixtures (15 minutes)

**Goal:** Create realistic JSON fixtures for all 6 endpoints

### Tasks

**T001: Create Collection Endpoint Fixtures**

Create 4 new fixture files in `tests/fixtures/`:

1. `procedurelogs_list.json` - Array of procedure log records
2. `allergies_list.json` - Array of allergy records  
3. `medicationpats_list.json` - Array of medication records
4. `diseases_list.json` - Array of disease/problem records

**T002: Create Single Resource Fixture**

5. `patientnotes_dict.json` - Single patient notes object (or reuse existing)

**T003: Create Query Endpoint Fixture**

6. `vitalsigns_list.json` - Array of vital signs query results

**T004: Create Empty List Fixtures**

7. `empty_list.json` - Empty array `[]` for testing no-records scenarios

**Checkpoint:** All fixtures created with realistic data matching CSV specifications

---

## Phase 1: Update Existing Contract Tests (30 minutes)

**Goal:** Update existing tests to verify response type (dict vs list)

### Tasks

**T005: Update test_api_client_golden_path.py**

File: `tests/contract/test_api_client_golden_path.py`

Update existing tests to verify response types:

```python
# For procedurelogs
async def test_fetch_procedure_logs_golden_path(api_credential, fixtures_dir):
    data = load_fixture(fixtures_dir, "procedurelogs_list.json")
    
    route = respx.get(...).mock(return_value=httpx.Response(200, json=data))
    
    response = await client.fetch_procedure_logs(99413)
    
    assert response.success is True
    assert response.http_status == 200
    assert isinstance(response.data, list)  # NEW: Verify type
    assert len(response.data) > 0  # NEW: Verify not empty
```

Update for:
- test_fetch_procedure_logs_golden_path ✅
- test_fetch_allergies_golden_path ✅
- test_fetch_medications_golden_path ✅
- test_fetch_problems_golden_path ✅

**T006: Update PatientNotes Test**

Verify patientnotes still returns dict:

```python
async def test_fetch_patient_notes_golden_path(api_credential, fixtures_dir):
    data = load_fixture(fixtures_dir, "patientnotes_dict.json")
    
    route = respx.get(...).mock(return_value=httpx.Response(200, json=data))
    
    response = await client.fetch_patient_notes(39689)
    
    assert response.success is True
    assert isinstance(response.data, dict)  # Verify dict type
    assert not isinstance(response.data, list)  # Explicitly NOT a list
```

**Checkpoint:** Existing tests updated and passing

---

## Phase 2: Add New Contract Tests (30 minutes)

**Goal:** Add comprehensive tests for list/dict response handling

### Tasks

**T007: Create test_api_client_list_responses.py**

New file: `tests/contract/test_api_client_list_responses.py`

Add tests specifically for list response validation:

```python
"""Contract tests for API endpoints returning list responses."""

import pytest
import httpx
import respx
from opendental_cli.api_client import OpenDentalAPIClient

@pytest.mark.asyncio
@respx.mock
async def test_procedurelogs_returns_list_of_dicts(api_credential, fixtures_dir):
    """Verify procedurelogs endpoint returns list of dictionaries."""
    data = load_fixture(fixtures_dir, "procedurelogs_list.json")
    
    respx.get("https://example.opendental.com/api/v1/procedurelogs?AptNum=99413").mock(
        return_value=httpx.Response(200, json=data)
    )
    
    client = OpenDentalAPIClient(api_credential)
    try:
        response = await client.fetch_procedure_logs(99413)
        
        # Verify response structure
        assert response.success is True
        assert response.http_status == 200
        assert response.endpoint_name == "procedurelogs"
        
        # Verify data type
        assert isinstance(response.data, list)
        assert len(response.data) >= 1
        
        # Verify list contains dicts
        for item in response.data:
            assert isinstance(item, dict)
            assert "ProcCode" in item
            assert "Descript" in item
    finally:
        await client.close()

@pytest.mark.asyncio
@respx.mock
async def test_allergies_returns_list_of_dicts(...):
    # Similar structure

@pytest.mark.asyncio
@respx.mock
async def test_medicationpats_returns_list_of_dicts(...):
    # Similar structure

@pytest.mark.asyncio
@respx.mock
async def test_diseases_returns_list_of_dicts(...):
    # Similar structure

@pytest.mark.asyncio
@respx.mock
async def test_empty_list_response_valid(...):
    """Verify endpoints handle empty list responses correctly."""
    respx.get(...).mock(return_value=httpx.Response(200, json=[]))
    
    response = await client.fetch_allergies(39689)
    
    assert response.success is True
    assert isinstance(response.data, list)
    assert len(response.data) == 0  # Empty list is valid
```

**T008: Create test_api_client_dict_responses.py**

New file: `tests/contract/test_api_client_dict_responses.py`

Add tests for dict response validation:

```python
"""Contract tests for API endpoints returning dict responses."""

@pytest.mark.asyncio
@respx.mock
async def test_patientnotes_returns_dict_not_list(api_credential, fixtures_dir):
    """Verify patientnotes returns single dict, not list."""
    data = load_fixture(fixtures_dir, "patientnotes_dict.json")
    
    respx.get("https://example.opendental.com/api/v1/patientnotes/39689").mock(
        return_value=httpx.Response(200, json=data)
    )
    
    client = OpenDentalAPIClient(api_credential)
    try:
        response = await client.fetch_patient_notes(39689)
        
        # Verify dict response
        assert isinstance(response.data, dict)
        assert not isinstance(response.data, list)
        
        # Verify structure
        assert "PatNum" in response.data
        assert "MedicalComp" in response.data
        assert response.data["PatNum"] == 39689
    finally:
        await client.close()
```

**T009: Create test_api_client_vital_signs.py**

New file: `tests/contract/test_api_client_vital_signs.py`

Add tests for VitalSigns endpoint:

```python
"""Contract tests for VitalSigns query endpoint."""

@pytest.mark.asyncio
@respx.mock
async def test_vitalsigns_success_returns_list(...):
    """Test VitalSigns with successful query response."""
    data = load_fixture(fixtures_dir, "vitalsigns_list.json")
    
    respx.put("https://example.opendental.com/api/v1/queries/ShortQuery").mock(
        return_value=httpx.Response(200, json=data)
    )
    
    response = await client.fetch_vital_signs(99413)
    
    assert response.success is True
    assert isinstance(response.data, list)
    # Verify SQL query was sent in body

@pytest.mark.asyncio
@respx.mock
async def test_vitalsigns_400_error_handling(...):
    """Test VitalSigns handles 400 Bad Request correctly."""
    respx.put(...).mock(return_value=httpx.Response(400, json={"error": "Bad SQL"}))
    
    response = await client.fetch_vital_signs(99413)
    
    assert response.success is False
    assert response.http_status == 400
    assert "Client error" in response.error_message
```

**Checkpoint:** All new contract tests created and passing

---

## Phase 3: Add Integration Tests (30 minutes)

**Goal:** Test full orchestration with mixed dict/list responses

### Tasks

**T010: Create test_endpoint_validation.py**

New file: `tests/integration/test_endpoint_validation.py`

```python
"""Integration tests for endpoint validation with mixed response types."""

import pytest
import httpx
import respx
from opendental_cli.orchestrator import orchestrate_retrieval
from opendental_cli.models.request import AuditDataRequest

@pytest.mark.asyncio
@respx.mock
async def test_orchestration_with_mixed_response_types(api_credential, fixtures_dir):
    """Test orchestration handles both list and dict responses."""
    
    # Mock all 6 endpoints
    respx.get(".../procedurelogs?AptNum=99413").mock(
        return_value=httpx.Response(200, json=load_fixture(..., "procedurelogs_list.json"))
    )
    respx.get(".../allergies?PatNum=39689").mock(
        return_value=httpx.Response(200, json=load_fixture(..., "allergies_list.json"))
    )
    respx.get(".../medicationpats?PatNum=39689").mock(
        return_value=httpx.Response(200, json=load_fixture(..., "medicationpats_list.json"))
    )
    respx.get(".../diseases?PatNum=39689").mock(
        return_value=httpx.Response(200, json=load_fixture(..., "diseases_list.json"))
    )
    respx.get(".../patientnotes/39689").mock(
        return_value=httpx.Response(200, json=load_fixture(..., "patientnotes_dict.json"))
    )
    respx.put(".../queries/ShortQuery").mock(
        return_value=httpx.Response(200, json=load_fixture(..., "vitalsigns_list.json"))
    )
    
    # Create request
    request = AuditDataRequest(patnum=39689, aptnum=99413)
    
    # Execute orchestration
    result = await orchestrate_retrieval(request, api_credential)
    
    # Verify all succeeded
    assert result.successful_count == 6
    assert result.failed_count == 0
    assert result.exit_code() == 0
    
    # Verify success dict contains both lists and dicts
    assert isinstance(result.success["procedurelogs"], list)
    assert isinstance(result.success["allergies"], list)
    assert isinstance(result.success["medicationpats"], list)
    assert isinstance(result.success["diseases"], list)
    assert isinstance(result.success["patientnotes"], dict)
    assert isinstance(result.success["vital_signs"], list)

@pytest.mark.asyncio
@respx.mock
async def test_partial_success_with_vitalsigns_failure(...):
    """Test orchestration with VitalSigns 400 error."""
    
    # Mock 5 successes
    # ... (same as above)
    
    # Mock VitalSigns failure
    respx.put(".../queries/ShortQuery").mock(
        return_value=httpx.Response(400, json={"error": "Bad SQL"})
    )
    
    result = await orchestrate_retrieval(request, api_credential)
    
    # Verify partial success
    assert result.successful_count == 5
    assert result.failed_count == 1
    assert result.exit_code() == 2  # Partial success
    
    # Verify failures list
    assert len(result.failures) == 1
    assert result.failures[0]["endpoint"] == "vital_signs"

@pytest.mark.asyncio
@respx.mock
async def test_empty_lists_handled_correctly(...):
    """Test orchestration with some endpoints returning empty lists."""
    
    # Mock with empty lists for allergies and medications
    respx.get(".../allergies?PatNum=39689").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.get(".../medicationpats?PatNum=39689").mock(
        return_value=httpx.Response(200, json=[])
    )
    # ... other endpoints with data
    
    result = await orchestrate_retrieval(request, api_credential)
    
    # Verify still considered successful
    assert result.successful_count == 6
    assert isinstance(result.success["allergies"], list)
    assert len(result.success["allergies"]) == 0
```

**T011: Update test_golden_path.py**

Update existing integration tests to verify response types:

```python
async def test_golden_path_stdout(...):
    # ... existing setup ...
    
    # NEW: Verify response types in consolidated data
    assert isinstance(consolidated.success["procedurelogs"], list)
    assert isinstance(consolidated.success["patientnotes"], dict)
```

**Checkpoint:** Integration tests verify full orchestration with mixed types

---

## Phase 4: Validation & Documentation (15 minutes)

**Goal:** Run all tests and document results

### Tasks

**T012: Run Full Test Suite**

```bash
pytest tests/ -v --tb=short
```

Expected results:
- All existing tests pass
- All new contract tests pass
- All integration tests pass
- Coverage remains 90%+

**T013: Run Specific Test Categories**

```bash
# Contract tests only
pytest tests/contract/ -v

# Integration tests only
pytest tests/integration/ -v

# New list response tests
pytest tests/contract/test_api_client_list_responses.py -v
```

**T014: Update Documentation**

Update `specs/003-endpoint-testing/research.md` with:
- Test results summary
- Any failures found
- Coverage metrics

**T015: Update Tasks File**

Mark all tasks complete in `specs/003-endpoint-testing/tasks.md`

**Checkpoint:** All tests passing, documentation complete

---

## Test Coverage Goals

### Target Coverage

- Overall: 90%+
- api_client.py: 95%+
- orchestrator.py: 95%+
- models/response.py: 100% (critical validation logic)

### Coverage Gaps to Fill

1. Empty list responses
2. Mixed success/failure scenarios
3. Authorization header with list responses
4. Error cases (404, 401, 500) with list responses

---

## Success Criteria

- [ ] All 6 JSON fixtures created
- [ ] Existing contract tests updated (6 tests)
- [ ] New contract tests added (10+ tests)
- [ ] Integration tests added (3+ tests)
- [ ] Full test suite passes
- [ ] Coverage remains 90%+
- [ ] Documentation updated

---

## Rollback Plan

If tests reveal issues with the dict|list fix:

1. Review specific failing test
2. Check if EndpointResponse model validation is correct
3. Verify fixtures match actual API responses
4. Consider if ConsolidatedAuditData needs adjustments

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Phase 0: Fixtures | 15 min | T001-T004 |
| Phase 1: Update Tests | 30 min | T005-T006 |
| Phase 2: New Tests | 30 min | T007-T009 |
| Phase 3: Integration | 30 min | T010-T011 |
| Phase 4: Validation | 15 min | T012-T015 |
| **Total** | **2 hours** | |

---

## Dependencies

- JSON fixtures must match actual API responses
- respx mocking must correctly simulate list/dict responses
- All tests must use mocking (no real API calls per Article IV)

---

## Notes

- Keep PHI out of fixtures (use fake data like "Test TestTest...")
- Verify Authorization header still sent correctly with list responses
- Consider adding performance tests later (out of scope for this phase)
