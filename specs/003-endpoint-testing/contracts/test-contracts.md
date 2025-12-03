# Test Contracts: API Endpoint Validation

**Feature**: 003-endpoint-testing  
**Purpose**: Define expected behavior and validation contracts for endpoint tests

---

## Contract 1: Collection Endpoint Response Structure

**Applies to:** ProcedureLogs, Allergies, MedicationPats, Diseases

### Request Format

```http
GET /fhir/v1/{resource}?PatientNum={patient_id}
Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}
```

### Response Contract

**Status Code:** `200 OK`

**Response Body:**
```json
[
  {
    "field1": "value1",
    "field2": "value2",
    ...
  },
  {
    "field1": "value3",
    "field2": "value4",
    ...
  }
]
```

**Type Contract:**
- Response MUST be JSON array
- Each element MUST be a JSON object
- Array MAY be empty `[]`
- Array elements MUST have consistent structure

### Pydantic Model Contract

```python
class EndpointResponse(BaseModel):
    success: bool = True
    data: list[dict[str, Any]]  # MUST accept list
    error: str | None = None
```

### Test Assertions

```python
# Type validation
assert isinstance(response.data, list)
assert all(isinstance(item, dict) for item in response.data)

# Structure validation
if len(response.data) > 0:
    assert len(response.data[0].keys()) > 0  # Has fields
    
# Model validation
response = EndpointResponse(success=True, data=api_response)
assert response.success is True
```

---

## Contract 2: Single Resource Endpoint Response Structure

**Applies to:** PatientNotes

### Request Format

```http
GET /fhir/v1/patientnotes?PatientNum={patient_id}
Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}
```

### Response Contract

**Status Code:** `200 OK`

**Response Body:**
```json
{
  "PatNum": 12345,
  "ICEName": "Test TestTest",
  "ICEPhone": "(555) 555-5555",
  ...
}
```

**Type Contract:**
- Response MUST be JSON object (not array)
- Object MUST have at least one field
- Object MUST NOT be wrapped in array

### Pydantic Model Contract

```python
class EndpointResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]  # MUST accept dict
    error: str | None = None
```

### Test Assertions

```python
# Type validation
assert isinstance(response.data, dict)
assert not isinstance(response.data, list)

# Structure validation
assert len(response.data.keys()) > 0  # Has fields
assert "PatNum" in response.data  # Required field

# Model validation
response = EndpointResponse(success=True, data=api_response)
assert response.success is True
```

---

## Contract 3: Query Endpoint Response Structure

**Applies to:** VitalSigns

### Request Format

```http
PUT /fhir/v1/vitals?PatientNum={patient_id}
Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}
Content-Type: application/json

{
  "query": "SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE PatNum = {patient_id}"
}
```

### Response Contract

**Success Status Code:** `200 OK`

**Success Response Body:**
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

**Error Status Code:** `400 Bad Request` (SQL syntax error)

**Error Response Body:**
```json
{
  "error": "SQL syntax error near '...'"
}
```

### Type Contract (Success)

- Response MUST be JSON array
- Each element MUST be a JSON object
- Array MAY be empty `[]`

### Test Assertions (Success)

```python
# Type validation
assert response.status_code == 200
assert isinstance(response.data, list)

# Structure validation
if len(response.data) > 0:
    assert "DateTaken" in response.data[0]
    assert "Pulse" in response.data[0]
```

### Test Assertions (Error)

```python
# Error handling
assert response.status_code == 400
assert response.success is False
assert response.error is not None
```

---

## Contract 4: Mixed Type Response Handling

**Applies to:** ConsolidatedAuditData (orchestration)

### Input Format

```python
{
    "PatientNum": 12345,
    "endpoints": [
        {"name": "ProcedureLogs", "data": [...]},  # list
        {"name": "Allergies", "data": [...]},       # list
        {"name": "PatientNotes", "data": {...}},    # dict
    ]
}
```

### Type Contract

```python
class ConsolidatedAuditData(BaseModel):
    patient_num: int
    success: dict[str, dict[str, Any] | list[dict[str, Any]]]  # Mixed types
    failed: dict[str, str]
```

### Test Assertions

```python
# Type flexibility
assert isinstance(result.success["ProcedureLogs"], list)
assert isinstance(result.success["Allergies"], list)
assert isinstance(result.success["PatientNotes"], dict)

# All types valid
for endpoint, data in result.success.items():
    assert isinstance(data, (dict, list))
```

---

## Contract 5: Empty Response Handling

**Applies to:** All collection endpoints

### Response Contract

**Status Code:** `200 OK`

**Response Body:**
```json
[]
```

### Type Contract

- Empty array `[]` is valid
- MUST NOT return `null` or `{}`
- MUST parse as list type

### Test Assertions

```python
# Empty list handling
assert isinstance(response.data, list)
assert len(response.data) == 0
assert response.success is True
```

---

## Contract 6: Error Response Handling

**Applies to:** All endpoints

### Response Contract

**Status Code:** `4xx` or `5xx`

**Response Body:**
```json
{
  "error": "Error message"
}
```

### Type Contract

```python
class EndpointResponse(BaseModel):
    success: bool = False
    data: None
    error: str
```

### Test Assertions

```python
# Error handling
assert response.success is False
assert response.data is None
assert response.error is not None
assert isinstance(response.error, str)
```

---

## Test Coverage Matrix

| Contract | Endpoint | Response Type | Test Status |
|----------|----------|---------------|-------------|
| Collection | ProcedureLogs | list | ⏳ To implement |
| Collection | Allergies | list | ⏳ To implement |
| Collection | MedicationPats | list | ⏳ To implement |
| Collection | Diseases | list | ⏳ To implement |
| Single Resource | PatientNotes | dict | ⏳ To implement |
| Query | VitalSigns | list | ⏳ To implement |
| Mixed Types | Orchestration | dict+list | ⏳ To implement |
| Empty | All collections | [] | ⏳ To implement |
| Error | All endpoints | error | ✅ Partially exists |

---

## Validation Rules

### Rule 1: Type Safety
- **MUST:** Use `isinstance()` checks before processing data
- **MUST:** Handle both dict and list types in ConsolidatedAuditData
- **MUST NOT:** Assume response type without validation

### Rule 2: Structure Validation
- **MUST:** Validate required fields exist
- **SHOULD:** Validate field types match expected schema
- **MAY:** Validate field value constraints

### Rule 3: Error Handling
- **MUST:** Handle HTTP 4xx/5xx errors gracefully
- **MUST:** Preserve error messages for debugging
- **MUST:** Set `success=False` on errors

### Rule 4: Edge Cases
- **MUST:** Handle empty lists `[]`
- **MUST:** Handle missing optional fields
- **SHOULD:** Handle malformed JSON
- **SHOULD:** Handle timeout scenarios

---

## Breaking Changes

### Before (BROKEN)

```python
# Only accepted dict
data: dict[str, Any] | None

# Failed on list responses
response = EndpointResponse(success=True, data=[...])
# ❌ Pydantic ValidationError: Input should be a valid dictionary
```

### After (FIXED)

```python
# Accepts dict OR list
data: dict[str, Any] | list[dict[str, Any]] | None

# Works with both
response = EndpointResponse(success=True, data=[...])  # ✅ OK
response = EndpointResponse(success=True, data={...})  # ✅ OK
```

---

## Implementation Checklist

- [ ] All fixtures match contract specifications
- [ ] All tests validate type contracts
- [ ] All tests validate structure contracts
- [ ] Error contracts tested
- [ ] Empty response contracts tested
- [ ] Mixed type contracts tested
- [ ] Breaking change documented
- [ ] All contracts verified passing
