# Research: API Endpoint Response Type Analysis

**Feature**: 003-endpoint-testing  
**Date**: 2025-12-02

## Executive Summary

Analysis of OpenDental API endpoint responses reveals two distinct patterns:
1. **Collection endpoints** return **arrays/lists** of objects
2. **Single resource endpoints** return **single dictionaries**

This research documents the exact response structures needed for comprehensive test coverage.

---

## Response Type Patterns

### Pattern 1: Collection Endpoints (List Response)

**Endpoints:**
- ProcedureLogs
- Allergies
- MedicationPats
- Diseases

**Response Structure:**
```json
[
  { /* object 1 */ },
  { /* object 2 */ },
  ...
]
```

**Python Type:** `list[dict[str, Any]]`

**Rationale:** These endpoints return multiple records related to a patient/appointment, so they naturally return arrays even if only one record exists (or zero records for empty arrays).

---

### Pattern 2: Single Resource Endpoint (Dict Response)

**Endpoint:**
- PatientNotes

**Response Structure:**
```json
{
  "PatNum": 39689,
  "MedicalComp": "...",
  ...
}
```

**Python Type:** `dict[str, Any]`

**Rationale:** Patient notes are a single composite record per patient, not a collection.

---

### Pattern 3: Query Endpoint (Special Case)

**Endpoint:**
- VitalSigns (via ShortQuery)

**Request:** `PUT /queries/ShortQuery` with SQL in body  
**Response:** Unknown (currently returns 400)  
**Expected:** Likely returns list of query results

---

## Detailed Response Specifications

### 1. ProcedureLogs Response

**Source:** CSV + User Output

**Structure:**
```json
[
  {
    "ProcNum": 563953,
    "ProcCode": "D0220",
    "Descript": "intraoral - periapical first radiographic image",
    "ProcFee": "31.00",
    "ProcStatus": "TP",
    "ProcDate": "2025-12-02 14:29:55"
  }
]
```

**Key Fields:**
- `ProcNum`: Procedure number (int)
- `ProcCode`: Procedure code (string)
- `Descript`: Description (string)
- `ProcFee`: Fee amount (string, decimal)
- `ProcStatus`: Status code (string)

**Type:** `list[dict[str, Any]]`

---

### 2. Allergies Response

**Source:** CSV + User Output

**Structure:**
```json
[
  {
    "AllergyNum": 2961,
    "AllergyDefNum": 11,
    "PatNum": 39689,
    "defDescription": "Environmental Allergies",
    "defSnomedType": "None",
    "Reaction": "Reaction",
    "StatusIsActive": "true",
    "DateAdverseReaction": "0001-01-01"
  }
]
```

**Key Fields:**
- `AllergyNum`: Allergy record ID (int)
- `defDescription`: Allergy description (string)
- `Reaction`: Reaction description (string)
- `StatusIsActive`: Active status (string boolean)

**Type:** `list[dict[str, Any]]`

---

### 3. MedicationPats Response

**Source:** CSV + User Output

**Structure:**
```json
[
  {
    "MedicationPatNum": 6537,
    "PatNum": 39689,
    "medName": "Antibiotic",
    "MedicationNum": 121,
    "PatNote": "Notes",
    "DateStart": "0001-01-01",
    "DateStop": "0001-01-01",
    "ProvNum": 0
  }
]
```

**Key Fields:**
- `MedicationPatNum`: Medication record ID (int)
- `medName`: Medication name (string)
- `PatNote`: Patient notes (string)

**Type:** `list[dict[str, Any]]`

**Note:** Inactive medications are not returned by API.

---

### 4. Diseases Response

**Source:** CSV + User Output

**Structure:**
```json
[
  {
    "DiseaseNum": 4811,
    "PatNum": 39689,
    "DiseaseDefNum": 92,
    "diseaseDefName": "Anemic",
    "PatNote": "dsasad",
    "ProbStatus": "Active",
    "DateStart": "0001-01-01",
    "DateStop": "0001-01-01"
  }
]
```

**Key Fields:**
- `DiseaseNum`: Disease record ID (int)
- `diseaseDefName`: Disease name (string)
- `PatNote`: Patient notes (string)
- `ProbStatus`: Problem status (string)

**Type:** `list[dict[str, Any]]`

---

### 5. PatientNotes Response

**Source:** CSV + User Output (WORKING)

**Structure:**
```json
{
  "PatNum": 39689,
  "FamFinancial": "",
  "Medical": "",
  "Service": "",
  "MedicalComp": "Test TestTestTestTestTestTestTestTestTest",
  "Treatment": "",
  "ICEName": "",
  "ICEPhone": "",
  "SecDateTEntry": "2025-11-28 15:20:51",
  "SecDateTEdit": "2025-11-29 11:00:02"
}
```

**Key Fields:**
- `PatNum`: Patient number (int)
- `MedicalComp`: Medical history composite (string)
- `ICEName`: Emergency contact name (string)
- `ICEPhone`: Emergency contact phone (string)

**Type:** `dict[str, Any]` (NOT a list!)

**Why Different?** Patient notes are a single composite record per patient, not a collection of individual notes.

---

### 6. VitalSigns Response

**Source:** CSV (Expected)

**Expected Structure:**
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

**Key Fields:**
- `DateTaken`: Timestamp (datetime string)
- `Pulse`: Pulse rate (int)
- `BP`: Blood pressure (string)
- `Height`: Height (float)
- `Weight`: Weight (float)

**Type:** Likely `list[dict[str, Any]]` (query result set)

**Current Status:** Returns 400 Bad Request (SQL query issue)

---

## Test Fixture Requirements

### Fixture 1: procedurelogs_list.json

```json
[
  {
    "ProcNum": 563953,
    "PatNum": 39689,
    "AptNum": 99413,
    "ProcCode": "D0220",
    "Descript": "intraoral - periapical first radiographic image",
    "ProcFee": "31.00",
    "ProcStatus": "TP",
    "ProcDate": "2025-12-02 14:29:55"
  },
  {
    "ProcNum": 563954,
    "PatNum": 39689,
    "AptNum": 99413,
    "ProcCode": "D0330",
    "Descript": "panoramic radiographic image",
    "ProcFee": "45.00",
    "ProcStatus": "C",
    "ProcDate": "2025-12-01 10:15:00"
  }
]
```

### Fixture 2: allergies_list.json

```json
[
  {
    "AllergyNum": 2961,
    "AllergyDefNum": 11,
    "PatNum": 39689,
    "defDescription": "Environmental Allergies",
    "defSnomedType": "None",
    "Reaction": "Hives",
    "StatusIsActive": "true",
    "DateAdverseReaction": "0001-01-01"
  },
  {
    "AllergyNum": 2962,
    "AllergyDefNum": 15,
    "PatNum": 39689,
    "defDescription": "Peanuts",
    "defSnomedType": "Food",
    "Reaction": "Anaphylaxis",
    "StatusIsActive": "true",
    "DateAdverseReaction": "2020-05-15"
  }
]
```

### Fixture 3: medicationpats_list.json

```json
[
  {
    "MedicationPatNum": 6537,
    "PatNum": 39689,
    "medName": "Antibiotic",
    "MedicationNum": 121,
    "PatNote": "Take twice daily",
    "DateStart": "2025-11-01",
    "DateStop": "2025-11-15",
    "ProvNum": 1
  },
  {
    "MedicationPatNum": 6538,
    "PatNum": 39689,
    "medName": "Ibuprofen",
    "MedicationNum": 42,
    "PatNote": "For pain as needed",
    "DateStart": "2025-11-01",
    "DateStop": "0001-01-01",
    "ProvNum": 1
  }
]
```

### Fixture 4: diseases_list.json

```json
[
  {
    "DiseaseNum": 4811,
    "PatNum": 39689,
    "DiseaseDefNum": 92,
    "diseaseDefName": "Anemic",
    "PatNote": "Mild iron deficiency",
    "ProbStatus": "Active",
    "DateStart": "2023-03-15",
    "DateStop": "0001-01-01"
  },
  {
    "DiseaseNum": 4812,
    "PatNum": 39689,
    "DiseaseDefNum": 45,
    "diseaseDefName": "Hypertension",
    "PatNote": "Controlled with medication",
    "ProbStatus": "Active",
    "DateStart": "2022-01-10",
    "DateStop": "0001-01-01"
  }
]
```

### Fixture 5: patientnotes_dict.json

```json
{
  "PatNum": 39689,
  "FamFinancial": "",
  "Medical": "",
  "Service": "",
  "MedicalComp": "Test TestTestTestTestTestTestTestTestTest",
  "Treatment": "",
  "ICEName": "Jane Doe",
  "ICEPhone": "(555) 123-4567",
  "SecDateTEntry": "2025-11-28 15:20:51",
  "SecDateTEdit": "2025-11-29 11:00:02"
}
```

### Fixture 6: vitalsigns_list.json

```json
[
  {
    "DateTaken": "2025-11-11T00:00:00",
    "Pulse": 122,
    "BP": "123/321",
    "Height": 231.0,
    "Weight": 98.0
  },
  {
    "DateTaken": "2025-11-10T00:00:00",
    "Pulse": 118,
    "BP": "120/80",
    "Height": 231.0,
    "Weight": 97.5
  }
]
```

---

## Test Case Matrix

| Endpoint | Response Type | Fixture | Mock URL | Status |
|----------|---------------|---------|----------|--------|
| ProcedureLogs | list | procedurelogs_list.json | /procedurelogs?AptNum=99413 | ✅ Ready |
| Allergies | list | allergies_list.json | /allergies?PatNum=39689 | ✅ Ready |
| MedicationPats | list | medicationpats_list.json | /medicationpats?PatNum=39689 | ✅ Ready |
| Diseases | list | diseases_list.json | /diseases?PatNum=39689 | ✅ Ready |
| PatientNotes | dict | patientnotes_dict.json | /patientnotes/39689 | ✅ Ready |
| VitalSigns | list | vitalsigns_list.json | /queries/ShortQuery | ⏳ Needs fix |

---

## Validation Strategy

### For List Responses

```python
def test_list_response(endpoint_name, response):
    # Type validation
    assert isinstance(response.data, list)
    assert all(isinstance(item, dict) for item in response.data)
    
    # Success validation
    assert response.success is True
    assert response.http_status == 200
    assert response.error_message is None
    
    # Structure validation
    assert len(response.data) > 0  # At least one record
    # Validate specific fields based on endpoint
```

### For Dict Response

```python
def test_dict_response(endpoint_name, response):
    # Type validation
    assert isinstance(response.data, dict)
    assert not isinstance(response.data, list)
    
    # Success validation
    assert response.success is True
    assert response.http_status == 200
    assert response.error_message is None
    
    # Structure validation
    assert "PatNum" in response.data
    assert "MedicalComp" in response.data
```

---

## Key Decisions

### Decision 1: Fixture Realism

**Options:**
- A. Use minimal fixtures (single records)
- B. Use realistic fixtures (multiple records with real-looking data)

**Decision:** Option B - Realistic fixtures

**Rationale:**
- Better represents actual API responses
- Helps identify edge cases (empty lists, multiple records)
- More useful for debugging

### Decision 2: Empty List Handling

**Question:** Should we test empty list responses?

**Decision:** Yes, add separate test cases

**Rationale:**
- Patient may have no allergies (valid scenario)
- Empty list `[]` is different from None
- Ensures model handles both cases

### Decision 3: VitalSigns Test Approach

**Options:**
- A. Test with expected 400 error
- B. Test with mocked 200 success
- C. Both

**Decision:** Option C - Both

**Rationale:**
- Test current behavior (400 error handling)
- Test expected behavior (200 with list response)
- Helps identify if fix is needed

---

## Next Steps

1. Create all 6 JSON fixtures in `tests/fixtures/`
2. Update existing contract tests to verify response types
3. Add new contract tests for list-specific scenarios
4. Add integration tests for mixed dict/list orchestration
5. Run full test suite and verify coverage
