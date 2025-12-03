# Quick Start: API Endpoint Testing

**Goal:** Validate that all API endpoints work correctly with dict/list response handling

## Immediate Actions

### Step 1: Create Test Fixtures (15 min)

Create these files in `tests/fixtures/`:

**1. procedurelogs_list.json**
```json
[
  {
    "ProcNum": 563953,
    "ProcCode": "D0220",
    "Descript": "intraoral - periapical first radiographic image",
    "ProcFee": "31.00",
    "ProcStatus": "TP"
  }
]
```

**2. allergies_list.json**
```json
[
  {
    "AllergyNum": 2961,
    "defDescription": "Environmental Allergies",
    "Reaction": "Hives",
    "StatusIsActive": "true"
  }
]
```

**3-4.** Similar for medicationpats and diseases (copy structure from research.md)

**5. patientnotes_dict.json** (already exists as patient_12345.json)

**6. vitalsigns_list.json**
```json
[
  {
    "DateTaken": "2025-11-11T00:00:00",
    "Pulse": 122,
    "BP": "123/321",
    "Height": 231.0,
    "Weight": 98.0
  }
]
```

### Step 2: Update Existing Tests (10 min)

**File:** `tests/contract/test_api_client_golden_path.py`

Add type assertions to existing tests:

```python
async def test_fetch_procedure_logs_golden_path(api_credential, fixtures_dir):
    # ... existing setup ...
    
    response = await client.fetch_procedure_logs(67890)
    
    assert response.success is True
    assert isinstance(response.data, list)  # ADD THIS
    assert len(response.data) > 0  # ADD THIS
```

Do same for:
- test_fetch_allergies_golden_path
- test_fetch_medications_golden_path  
- test_fetch_problems_golden_path

For patientnotes:
```python
assert isinstance(response.data, dict)  # Verify dict, not list
```

### Step 3: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run just contract tests
pytest tests/contract/test_api_client_golden_path.py -v

# Check coverage
pytest --cov=src/opendental_cli tests/ --cov-report=term
```

### Step 4: Verify Results

**Expected:**
- ✅ All existing tests pass
- ✅ New type assertions pass (list for collections, dict for patientnotes)
- ✅ No Pydantic validation errors

**If failures occur:**
- Check fixture format matches actual API response
- Verify `EndpointResponse.data` type is `dict | list | None`
- Check that existing fixtures are lists not dicts

---

## Full Implementation (2 hours)

Follow the complete plan in `plan.md`:

**Phase 0:** Create all fixtures (15 min)  
**Phase 1:** Update existing tests (30 min)  
**Phase 2:** Add new contract tests (30 min)  
**Phase 3:** Add integration tests (30 min)  
**Phase 4:** Validate and document (15 min)

---

## Test Matrix

| Endpoint | Type | Fixture | Test Status |
|----------|------|---------|-------------|
| ProcedureLogs | list | procedurelogs_list.json | ⏳ Needs fixture |
| Allergies | list | allergies_list.json | ⏳ Needs fixture |
| MedicationPats | list | medicationpats_list.json | ⏳ Needs fixture |
| Diseases | list | diseases_list.json | ⏳ Needs fixture |
| PatientNotes | dict | patient_12345.json | ✅ Exists |
| VitalSigns | list | vitalsigns_list.json | ⏳ Needs fixture |

---

## Common Issues

### Issue 1: Test Expects Dict, Gets List

**Error:** `AssertionError: assert False (isinstance(list, dict))`

**Fix:** Update test to expect list:
```python
assert isinstance(response.data, list)
```

### Issue 2: Fixture Format Wrong

**Error:** `Pydantic validation error: Input should be a valid dictionary`

**Fix:** Ensure collection endpoints use array format:
```json
[{...}]  // ✅ Correct
{...}    // ❌ Wrong
```

### Issue 3: Empty Response

**Error:** `AssertionError: assert 0 > 0`

**Fix:** Allow empty lists:
```python
assert isinstance(response.data, list)
assert len(response.data) >= 0  # Allow empty
```

---

## Success Checklist

- [ ] All 6 fixtures created
- [ ] Existing tests updated with type checks
- [ ] New contract tests added (10+)
- [ ] Integration tests added (3+)
- [ ] Full test suite passes
- [ ] Coverage 90%+
- [ ] No Pydantic validation errors
- [ ] Documentation updated

---

## Next Steps After Testing

1. **If all pass:** Mark feature complete, update main README
2. **If VitalSigns fails:** Investigate 400 error, try different SQL formats
3. **If type errors:** Review EndpointResponse model, check fixture formats
4. **If coverage low:** Add edge case tests (empty lists, errors, etc.)
