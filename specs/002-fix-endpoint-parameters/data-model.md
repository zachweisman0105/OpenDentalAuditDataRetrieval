# Data Model: API Endpoint Specifications

**Feature**: 002-fix-endpoint-parameters  
**Date**: 2025-12-02

## Endpoint Specifications from CSV

### 1. ProcedureLogs

**Request:**
- Method: `GET`
- URL: `/api/v1/procedurelogs?AptNum={aptnum}`
- Parameter: AptNum (Appointment Number)

**Response Fields:**
```json
{
  "ProcCode": "D0220",
  "Descript": "intraoral - periapical first radiographic image",
  "ProcFee": "31.00",
  "ProcStatus": "TP"
}
```

**Current Implementation:** ✅ CORRECT
```python
f"/procedurelogs?AptNum={aptnum}"
```

---

### 2. Allergies

**Request:**
- Method: `GET`
- URL: `/api/v1/allergies?PatNum={patnum}`
- Parameter: PatNum (Patient Number)

**Response Fields:**
```json
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
```

**Current Implementation:** ✅ CORRECT
```python
f"/allergies?PatNum={patnum}"
```

---

### 3. MedicationPats

**Request:**
- Method: `GET`
- URL: `/api/v1/medicationpats?PatNum={patnum}`
- Parameter: PatNum (Patient Number)

**Response Fields:**
```json
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
```

**Note from CSV:** "Inactive Medications are not returned"

**Current Implementation:** ✅ CORRECT
```python
f"/medicationpats?PatNum={patnum}"
```

---

### 4. Diseases (Problems)

**Request:**
- Method: `GET`
- URL: `/api/v1/diseases?PatNum={patnum}`
- Parameter: PatNum (Patient Number)

**Response Fields:**
```json
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
```

**Current Implementation:** ✅ CORRECT
```python
f"/diseases?PatNum={patnum}"
```

---

### 5. PatientNotes (Medical Info)

**Request:**
- Method: `GET`
- URL: `/api/v1/patientnotes` + `{PatNum}`
- Parameter: PatNum (Patient Number)
- **CSV Note:** "PatNum is required to be in the URL"

**Response Fields:**
```json
{
  "PatNum": 39689,
  "FamFinancial": "",
  "Medical": "",
  "Service": "",
  "MedicalComp": "Medical History",
  "Treatment": "",
  "ICEName": "",
  "ICEPhone": "",
  "SecDateTEntry": "2025-11-28 15:20:51",
  "SecDateTEdit": "2025-11-28 15:43:31"
}
```

**Current Implementation:** ❓ NEEDS VERIFICATION
```python
f"/patientnotes/{patnum}"  # Path parameter
```

**Alternative:**
```python
f"/patientnotes?PatNum={patnum}"  # Query parameter (consistent with others)
```

**Analysis:**
- CSV says "PatNum is required to be in the URL" - ambiguous
- All other endpoints use query parameters (`?PatNum=` or `?AptNum=`)
- REST convention for single resource: path parameter (`/resource/{id}`)
- OpenDental API may follow query parameter pattern for consistency

**Recommendation:** Test both formats to determine correct one

---

### 6. VitalSigns (Queries)

**Request:**
- Method: `PUT`
- URL: `/api/v1/queries/ShortQuery`
- Parameter: AptNum (in query body)
- Body: SQL query as JSON

**Response Fields:**
```json
{
  "DateTaken": "2025-11-11T00:00:00",
  "Pulse": 122,
  "BP": "123/321",
  "Height": 231.0,
  "Weight": 98.0
}
```

**CSV Note:** "BMI calculation needed: (Weight/Height^2)*703"

**Current Implementation:** ❓ NEEDS VERIFICATION
```python
query_body = {
    "query": f"SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE AptNum={aptnum}"
}
# PUT /queries/ShortQuery with json=query_body
```

**Potential Issues:**
1. Table name: `vitalsign` vs `vital_signs` vs `VitalSign`
2. Column case sensitivity: `DateTaken` vs `datetaken`
3. WHERE clause format: `WHERE AptNum={aptnum}` vs `WHERE AptNum = {aptnum}`
4. SQL dialect differences

**Recommendation:** Capture exact error message to determine issue

---

## Authorization Header (Already Fixed)

All endpoints now use:
```http
Authorization: ODFHIR {DeveloperKey}/{DeveloperPortalKey}
```

This was fixed in the previous feature (specs/main/).

---

## Validation Rules

### PatNum (Patient Number)
- Type: `int`
- Validation: Must be > 0
- Example: 39689

### AptNum (Appointment Number)
- Type: `int`
- Validation: Must be > 0
- Example: 99413

---

## Error Responses

### 401 Unauthorized
- Cause: Invalid or missing authorization
- Fix: Verify ODFHIR authorization header format

### 404 Not Found
- Cause: Wrong URL path or resource doesn't exist
- Fix: Check endpoint URL format (path vs query parameter)

### 400 Bad Request
- Cause: Malformed request or invalid parameters
- Fix: Verify SQL syntax for VitalSigns, check parameter format

### 500 Internal Server Error
- Cause: Backend error (SQL syntax, database issues)
- Fix: Check SQL query structure, table/column names

---

## Testing Matrix

| Endpoint | Test PatNum | Test AptNum | Expected Status | Fields to Validate |
|----------|-------------|-------------|-----------------|-------------------|
| ProcedureLogs | - | 99413 | 200 OK | ProcCode, Descript |
| Allergies | 39689 | - | 200 OK | defDescription, Reaction |
| MedicationPats | 39689 | - | 200 OK | medName, PatNote |
| Diseases | 39689 | - | 200 OK | diseaseDefName, ProbStatus |
| PatientNotes | 39689 | - | 200 OK | MedicalComp |
| VitalSigns | - | 99413 | 200 OK | Pulse, BP, Height, Weight |

---

## Implementation Summary

### Working Endpoints (High Confidence)
1. ✅ ProcedureLogs - Uses AptNum query parameter
2. ✅ Allergies - Uses PatNum query parameter
3. ✅ MedicationPats - Uses PatNum query parameter
4. ✅ Diseases - Uses PatNum query parameter

### Needs Verification
5. ❓ PatientNotes - Path vs query parameter ambiguity
6. ❓ VitalSigns - SQL query syntax uncertainty
