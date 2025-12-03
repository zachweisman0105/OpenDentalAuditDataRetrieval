# Data Model: API Endpoint Testing

**Feature**: 003-endpoint-testing  
**Purpose**: Define data structures for endpoint testing and validation

---

## 1. Test Fixture Data Models

### 1.1 ProcedureLog List Item

**Purpose:** Represents a single procedure log entry  
**API Response Type:** Element of array

```python
{
    "ProcNum": int,           # Primary key, unique identifier
    "ProcCode": str,          # Procedure code (e.g., "D0220")
    "Descript": str,          # Human-readable description
    "ProcFee": str,           # Fee amount as string (e.g., "31.00")
    "ProcStatus": str         # Status code (e.g., "TP", "C", "EC")
}
```

**Example:**
```json
{
  "ProcNum": 563953,
  "ProcCode": "D0220",
  "Descript": "intraoral - periapical first radiographic image",
  "ProcFee": "31.00",
  "ProcStatus": "TP"
}
```

### 1.2 Allergy List Item

**Purpose:** Represents a single allergy entry  
**API Response Type:** Element of array

```python
{
    "AllergyNum": int,        # Primary key, unique identifier
    "defDescription": str,     # Allergy type/category
    "Reaction": str,          # Patient reaction description
    "StatusIsActive": str      # "true" or "false" as string
}
```

**Example:**
```json
{
  "AllergyNum": 2961,
  "defDescription": "Environmental Allergies",
  "Reaction": "Hives",
  "StatusIsActive": "true"
}
```

### 1.3 MedicationPat List Item

**Purpose:** Represents a single medication entry  
**API Response Type:** Element of array

```python
{
    "MedicationPatNum": int,   # Primary key, unique identifier
    "MedicationNum": int,      # FK to medication definition
    "PatNum": int,             # FK to patient
    "RxCui": int,              # RxNorm Concept Unique Identifier
    "DateStart": str,          # ISO date string
    "DateStop": str | None,    # ISO date string or null
    "genericName": str,        # Generic medication name
    "notes": str               # Dosage and notes
}
```

**Example:**
```json
{
  "MedicationPatNum": 36,
  "MedicationNum": 32,
  "PatNum": 12345,
  "RxCui": 8163,
  "DateStart": "2024-01-15T00:00:00",
  "DateStop": null,
  "genericName": "warfarin sodium",
  "notes": "2mg daily"
}
```

### 1.4 Disease List Item

**Purpose:** Represents a single disease/problem entry  
**API Response Type:** Element of array

```python
{
    "DiseaseNum": int,         # Primary key, unique identifier
    "DiseaseDefNum": int,      # FK to disease definition
    "PatNum": int,             # FK to patient
    "PatNote": str,            # Clinical notes
    "ProbStatus": str,         # Status code (e.g., "Active", "Resolved")
    "DateStart": str,          # ISO date string
    "DateStop": str | None,    # ISO date string or null
    "SnomedProblemType": str,  # SNOMED CT problem type
    "DiseaseName": str         # Human-readable disease name
}
```

**Example:**
```json
{
  "DiseaseNum": 123,
  "DiseaseDefNum": 456,
  "PatNum": 12345,
  "PatNote": "Chronic condition, stable",
  "ProbStatus": "Active",
  "DateStart": "2023-06-01T00:00:00",
  "DateStop": null,
  "SnomedProblemType": "Problem",
  "DiseaseName": "Hypertension"
}
```

### 1.5 PatientNotes Object

**Purpose:** Represents patient emergency contact and notes  
**API Response Type:** Single object (NOT array)

```python
{
    "PatNum": int,             # Primary key, unique identifier
    "ICEName": str,            # Emergency contact name
    "ICEPhone": str,           # Emergency contact phone
    "AdmissionNote": str,      # Admission notes
    "FamFinUrgNote": str,      # Family financial urgent note
    "OrthoMonthsTreatOverride": int,  # Orthodontic treatment months
    "DateOrthoPlacementOverride": str,  # ISO date string
    "MedUrgNote": str          # Medical urgent note
}
```

**Example:**
```json
{
  "PatNum": 12345,
  "ICEName": "Test TestTest",
  "ICEPhone": "(555) 555-5555",
  "AdmissionNote": "",
  "FamFinUrgNote": "",
  "OrthoMonthsTreatOverride": -1,
  "DateOrthoPlacementOverride": "0001-01-01T00:00:00",
  "MedUrgNote": ""
}
```

### 1.6 VitalSign List Item

**Purpose:** Represents a single vital signs measurement  
**API Response Type:** Element of array

```python
{
    "DateTaken": str,          # ISO datetime string
    "Pulse": int,              # Beats per minute
    "BP": str,                 # Blood pressure (e.g., "120/80")
    "Height": float,           # Height in inches
    "Weight": float            # Weight in pounds
}
```

**Example:**
```json
{
  "DateTaken": "2025-11-11T00:00:00",
  "Pulse": 122,
  "BP": "123/321",
  "Height": 231.0,
  "Weight": 98.0
}
```

---

## 2. Response Wrapper Models

### 2.1 EndpointResponse (Updated)

**Purpose:** Wraps API endpoint responses with success/error metadata  
**Change:** Now accepts dict OR list for data field

```python
class EndpointResponse(BaseModel):
    """Response wrapper for API endpoint calls"""
    
    success: bool = True
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    error: str | None = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )
```

**Usage:**
```python
# List response (collection endpoints)
response = EndpointResponse(
    success=True,
    data=[{"ProcNum": 1}, {"ProcNum": 2}]
)

# Dict response (single resource)
response = EndpointResponse(
    success=True,
    data={"PatNum": 12345, "ICEName": "Test"}
)

# Error response
response = EndpointResponse(
    success=False,
    error="HTTP 400: Bad Request"
)
```

### 2.2 ConsolidatedAuditData (Updated)

**Purpose:** Aggregates results from multiple endpoints  
**Change:** Now accepts dict OR list for each endpoint's data

```python
class ConsolidatedAuditData(BaseModel):
    """Consolidated audit data from multiple endpoints"""
    
    patient_num: int
    success: dict[str, dict[str, Any] | list[dict[str, Any]]]
    failed: dict[str, str]
    
    model_config = ConfigDict(
        populate_by_name=True
    )
```

**Usage:**
```python
result = ConsolidatedAuditData(
    patient_num=12345,
    success={
        "ProcedureLogs": [{"ProcNum": 1}, {"ProcNum": 2}],  # list
        "Allergies": [{"AllergyNum": 3}],                    # list
        "PatientNotes": {"PatNum": 12345, "ICEName": "..."}  # dict
    },
    failed={
        "VitalSigns": "HTTP 400: SQL syntax error"
    }
)
```

---

## 3. Test Assertion Models

### 3.1 Type Assertion

**Purpose:** Validate response type matches expected pattern

```python
class TypeAssertion:
    """Validates response type"""
    
    @staticmethod
    def assert_list_response(response: EndpointResponse):
        assert isinstance(response.data, list)
        assert all(isinstance(item, dict) for item in response.data)
    
    @staticmethod
    def assert_dict_response(response: EndpointResponse):
        assert isinstance(response.data, dict)
        assert not isinstance(response.data, list)
    
    @staticmethod
    def assert_empty_list(response: EndpointResponse):
        assert isinstance(response.data, list)
        assert len(response.data) == 0
```

### 3.2 Structure Assertion

**Purpose:** Validate response structure matches expected schema

```python
class StructureAssertion:
    """Validates response structure"""
    
    @staticmethod
    def assert_procedure_log(data: dict):
        required_fields = ["ProcNum", "ProcCode", "Descript"]
        for field in required_fields:
            assert field in data
    
    @staticmethod
    def assert_allergy(data: dict):
        required_fields = ["AllergyNum", "defDescription"]
        for field in required_fields:
            assert field in data
    
    @staticmethod
    def assert_patient_notes(data: dict):
        required_fields = ["PatNum", "ICEName", "ICEPhone"]
        for field in required_fields:
            assert field in data
```

---

## 4. Test Fixture File Models

### 4.1 Fixture File Naming Convention

```
tests/fixtures/{resource}_{type}.json
```

**Examples:**
- `procedurelogs_list.json` - Array of procedure logs
- `allergies_list.json` - Array of allergies
- `patientnotes_dict.json` - Single patient notes object
- `empty_list.json` - Empty array `[]`

### 4.2 Fixture Data Requirements

**All fixtures MUST:**
1. Use placeholder data (no real PHI)
2. Match actual API response structure
3. Include required fields
4. Use correct data types
5. Follow JSON formatting standards

**Example placeholders:**
- Names: "Test TestTest", "Sample Patient"
- Phones: "(555) 555-5555"
- Addresses: "123 Test St"
- Dates: ISO 8601 format "2024-01-01T00:00:00"

---

## 5. Response Type Mapping

| Endpoint | HTTP Method | Response Type | Fixture File |
|----------|-------------|---------------|--------------|
| ProcedureLogs | GET | list[dict] | procedurelogs_list.json |
| Allergies | GET | list[dict] | allergies_list.json |
| MedicationPats | GET | list[dict] | medicationpats_list.json |
| Diseases | GET | list[dict] | diseases_list.json |
| PatientNotes | GET | dict | patientnotes_dict.json |
| VitalSigns | PUT | list[dict] | vitalsigns_list.json |

---

## 6. State Transitions

### 6.1 Test Execution Flow

```
1. Setup Phase
   └─> Load fixture from JSON file
   └─> Parse fixture data
   └─> Create mock HTTP response

2. Execution Phase
   └─> Call API client method
   └─> Receive EndpointResponse

3. Validation Phase
   └─> Assert response.success == True
   └─> Assert response.data type (list or dict)
   └─> Assert response.data structure
   └─> Assert response.error is None

4. Teardown Phase
   └─> Clean up mock
   └─> Report results
```

### 6.2 Error Handling Flow

```
1. Mock Error Response
   └─> HTTP 400/404/500/503 status

2. API Client Handling
   └─> Catch exception
   └─> Create EndpointResponse with error

3. Validation Phase
   └─> Assert response.success == False
   └─> Assert response.data is None
   └─> Assert response.error is not None
   └─> Assert error message meaningful
```

---

## 7. Breaking Change Documentation

### Before (BROKEN)

```python
class EndpointResponse(BaseModel):
    data: dict[str, Any] | None = None
```

**Problem:**
- Could not accept list responses
- Caused Pydantic validation errors
- Failed on collection endpoints

### After (FIXED)

```python
class EndpointResponse(BaseModel):
    data: dict[str, Any] | list[dict[str, Any]] | None = None
```

**Solution:**
- Accepts both dict and list
- No validation errors
- Works with all endpoint types

---

## Summary

**Data Models Created:** 11
- 6 fixture item models
- 2 response wrapper models
- 2 assertion models
- 1 state transition model

**Key Change:**
- `EndpointResponse.data` now accepts `dict | list` union type
- `ConsolidatedAuditData.success` now accepts mixed dict/list values

**Testing Coverage:**
- All 6 endpoint types modeled
- Empty response case modeled
- Error response case modeled
- Mixed type aggregation modeled
