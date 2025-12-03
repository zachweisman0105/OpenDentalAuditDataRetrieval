# Quick Start Guide: Diagnosing Endpoint Failures

**Goal**: Identify which of the 6 API endpoints are failing after ODFHIR authorization fix

## Option 1: Quick Manual Test (Recommended)

Run the CLI and check the output/logs:

```bash
opendental-cli --patnum 39689 --aptnum 99413 --output test_output.json
```

**Check the logs:**
```bash
cat audit.log | findstr "endpoint"
```

Look for patterns like:
- ✅ `"Endpoint succeeded"` - Working endpoint
- ❌ `"Endpoint failed"` - Failing endpoint
- Check `http_status` values (200 = success, 401 = auth, 404 = not found, etc.)

## Option 2: Run Diagnostic Script

```bash
python scripts/test_individual_endpoints.py
```

**Note**: Update the script with your actual credentials first:
1. Open `scripts/test_individual_endpoints.py`
2. Replace `test_dev_key` and `test_portal_key` with real values
3. Update `base_url` if different from `https://api.opendental.com/api/v1`

## What to Look For

### Expected Results Matrix

| Endpoint | Status | If Failed, Check |
|----------|--------|------------------|
| ProcedureLogs | ❓ | Uses `AptNum={aptnum}` - should work |
| Allergies | ❓ | Uses `PatNum={patnum}` - should work |
| MedicationPats | ❓ | Uses `PatNum={patnum}` - should work |
| Diseases | ❓ | Uses `PatNum={patnum}` - should work |
| PatientNotes | ❓ | Uses `/patientnotes/{patnum}` - may need query param |
| VitalSigns | ❓ | Uses SQL query - may have syntax error |

### Common Error Patterns

**401 Unauthorized:**
- Authorization header still incorrect
- Check if ODFHIR fix was applied: `Authorization: ODFHIR key1/key2`

**404 Not Found:**
- Wrong URL path (e.g., PatientNotes using path vs query parameter)
- Base URL missing `/api/v1` prefix

**400 Bad Request:**
- Malformed request (likely VitalSigns SQL query)
- Missing required parameters

**500 Internal Server Error:**
- Backend error (likely VitalSigns SQL syntax)
- Check table/column names in SQL query

## Quick Fixes Based on Errors

### If PatientNotes returns 404:

Try changing from path parameter to query parameter:

**File**: `src/opendental_cli/api_client.py` (line ~334)

Change:
```python
return await self.fetch_endpoint("patientnotes", f"/patientnotes/{patnum}")
```

To:
```python
return await self.fetch_endpoint("patientnotes", f"/patientnotes?PatNum={patnum}")
```

### If VitalSigns returns 400/500:

Check the SQL query construction in `api_client.py` (line ~344):

Current query:
```python
query_body = {
    "query": f"SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum={aptnum}"
}
```

Try:
1. Different table name: `vital_signs` or `VitalSigns`
2. Lowercase columns: `datetaken, pulse, bp, height, weight`
3. Add spaces in WHERE: `WHERE AptNum = {aptnum}`

## Next Steps After Diagnosis

1. **Capture Results**: Note which endpoints succeed/fail and their error messages
2. **Update research.md**: Document actual test results
3. **Apply Fixes**: Based on error patterns, update api_client.py
4. **Re-test**: Run diagnostic again to verify fixes
5. **Update Tests**: Modify contract tests to match working formats
