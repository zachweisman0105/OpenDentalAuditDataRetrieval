# OpenDental API Contracts

**Phase**: 1 - Design  
**Date**: 2025-11-29  
**Purpose**: Define API contracts for OpenDental REST API endpoints

## Base Configuration

**Base URL**: `https://{server}/api/v1/`  
**Authentication**: Custom Headers  
**Headers**: 
- `DeveloperKey: {developer_key}`
- `CustomerKey: {customer_key}`
**Content-Type**: `application/json`  
**TLS Version**: 1.2+  

---

## 1. Get Procedure Logs

**Endpoint**: `GET /procedurelogs?AptNum={AptNum}`  
**Purpose**: Retrieve procedure codes and logs for a specific appointment

### Request

```http
GET /api/v1/procedurelogs?AptNum=67890 HTTP/1.1
Host: example.opendental.com
DeveloperKey: YOUR_DEVELOPER_KEY
CustomerKey: YOUR_CUSTOMER_KEY
Accept: application/json
```

### Query Parameters

- `AptNum` (required): Appointment number to retrieve procedure logs

### Response (200 OK)

```json
{
  "AptNum": 67890,
  "procedures": [
    {
      "ProcCode": "D0120",
      "Descript": "Periodic oral evaluation",
      "ProcFee": 150.00,
      "ProcStatus": "C"
    },
    {
      "ProcCode": "D1110",
      "Descript": "Prophylaxis - adult",
      "ProcFee": 95.00,
      "ProcStatus": "C"
    }
  ]
}
```

### Error Responses

**404 Not Found**:
```json
{
  "error": "Appointment not found",
  "code": "APPOINTMENT_NOT_FOUND"
}
```

**401 Unauthorized**:
```json
{
  "error": "Invalid API key",
  "code": "UNAUTHORIZED"
}
```

**403 Forbidden**:
```json
{
  "error": "Insufficient permissions to access procedure logs",
  "code": "FORBIDDEN"
}
```

---

## 2. Get Allergies

**Endpoint**: `GET /allergies?PatNum={PatNum}`  
**Purpose**: Retrieve patient allergy information and status

### Request

```http
GET /api/v1/allergies?PatNum=12345 HTTP/1.1
Host: example.opendental.com
DeveloperKey: YOUR_DEVELOPER_KEY
CustomerKey: YOUR_CUSTOMER_KEY
Accept: application/json
```

### Query Parameters

- `PatNum` (required): Patient number to retrieve allergies

### Response (200 OK)

```json
{
  "PatNum": 12345,
  "allergies": [
    {
      "AllergyNum": 101,
      "AllergyDefNum": 25,
      "PatNum": 12345,
      "defDescription": "Penicillin",
      "Reaction": "Hives and difficulty breathing",
      "StatusIsActive": true,
      "defSnomedType": "medication",
      "DateAdverseReaction": "2020-05-15"
    },
    {
      "AllergyNum": 102,
      "AllergyDefNum": 42,
      "PatNum": 12345,
      "defDescription": "Latex",
      "Reaction": "Skin irritation",
      "StatusIsActive": true,
      "defSnomedType": "material",
      "DateAdverseReaction": "2018-03-22"
    }
  ]
}
```

### Error Responses

**404 Not Found**:
```json
{
  "error": "Patient not found",
  "code": "PATIENT_NOT_FOUND"
}
```

**401 Unauthorized**:
```json
{
  "error": "Invalid API key",
  "code": "UNAUTHORIZED"
}
```

**403 Forbidden**:
```json
{
  "error": "Insufficient permissions to access allergy data",
  "code": "FORBIDDEN"
}
```

---

## 3. Get Medications

**Endpoint**: `GET /medicationpats?PatNum={PatNum}`  
**Purpose**: Retrieve patient's active medications

**Note**: Inactive medications are NOT returned by this endpoint.

### Request

```http
GET /api/v1/medicationpats?PatNum=12345 HTTP/1.1
Host: example.opendental.com
DeveloperKey: YOUR_DEVELOPER_KEY
CustomerKey: YOUR_CUSTOMER_KEY
Accept: application/json
```

### Query Parameters

- `PatNum` (required): Patient number to retrieve medications

### Response (200 OK)

```json
{
  "PatNum": 12345,
  "medications": [
    {
      "MedicationPatNum": 201,
      "PatNum": 12345,
      "MedicationNum": 45,
      "medName": "Lisinopril 10mg",
      "PatNote": "Take once daily in the morning",
      "DateStart": "2024-06-01",
      "DateStop": null,
      "ProvNum": 5
    },
    {
      "MedicationPatNum": 202,
      "PatNum": 12345,
      "MedicationNum": 78,
      "medName": "Ibuprofen 400mg",
      "PatNote": "As needed for pain",
      "DateStart": "2025-11-15",
      "DateStop": "2025-11-22",
      "ProvNum": 5
    }
  ]
}
```

### Error Responses

**404 Not Found**:
```json
{
  "error": "Patient not found",
  "code": "PATIENT_NOT_FOUND"
}
```

**401 Unauthorized**:
```json
{
  "error": "Invalid API key",
  "code": "UNAUTHORIZED"
}
```

**403 Forbidden**:
```json
{
  "error": "Insufficient permissions to access medication data",
  "code": "FORBIDDEN"
}
```

---

## 4. Get Problems/Diseases

**Endpoint**: `GET /diseases?PatNum={PatNum}`  
**Purpose**: Retrieve patient's medical problems and disease history

### Request

```http
GET /api/v1/diseases?PatNum=12345 HTTP/1.1
Host: example.opendental.com
DeveloperKey: YOUR_DEVELOPER_KEY
CustomerKey: YOUR_CUSTOMER_KEY
Accept: application/json
```

### Query Parameters

- `PatNum` (required): Patient number to retrieve disease information

### Response (200 OK)

```json
{
  "PatNum": 12345,
  "diseases": [
    {
      "DiseaseNum": 301,
      "PatNum": 12345,
      "DiseaseDefNum": 18,
      "diseaseDefName": "Hypertension",
      "PatNote": "Controlled with medication",
      "ProbStatus": "Active",
      "DateStart": "2020-03-10",
      "DateStop": null
    },
    {
      "DiseaseNum": 302,
      "PatNum": 12345,
      "DiseaseDefNum": 25,
      "diseaseDefName": "Type 2 Diabetes",
      "PatNote": "Diet and exercise management",
      "ProbStatus": "Active",
      "DateStart": "2019-08-22",
      "DateStop": null
    }
  ]
}
```

### Error Responses

**404 Not Found**:
```json
{
  "error": "Patient not found",
  "code": "PATIENT_NOT_FOUND"
}
```

**401 Unauthorized**:
```json
{
  "error": "Invalid API key",
  "code": "UNAUTHORIZED"
}
```

**403 Forbidden**:
```json
{
  "error": "Insufficient permissions to access disease data",
  "code": "FORBIDDEN"
}
```

---

## 5. Get Patient Notes

**Endpoint**: `GET /patientnotes/{PatNum}`  
**Purpose**: Retrieve comprehensive patient notes including medical, financial, and emergency contact information

**Note**: PatNum is required in the URL path (not as a query parameter).

### Request

```http
GET /api/v1/patientnotes/12345 HTTP/1.1
Host: example.opendental.com
DeveloperKey: YOUR_DEVELOPER_KEY
CustomerKey: YOUR_CUSTOMER_KEY
Accept: application/json
```

### Path Parameters

- `PatNum` (required): Patient number in URL path

### Response (200 OK)

```json
{
  "PatNum": 12345,
  "MedicalComp": "Hypertension, Type 2 Diabetes",
  "Medical": "Patient reports good medication compliance. No recent complications.",
  "Service": "Patient prefers morning appointments. Reminder calls appreciated.",
  "Treatment": "Continue preventive care. Monitor blood pressure at each visit.",
  "FamFinancial": "Patient enrolled in payment plan for outstanding balance.",
  "ICEName": "Jane Doe",
  "ICEPhone": "(555) 987-6543",
  "SecDateTEntry": "2020-01-15T10:30:00Z",
  "SecDateTEdit": "2025-11-20T14:15:00Z"
}
```

### Error Responses

**404 Not Found**:
```json
{
  "error": "Patient notes not found",
  "code": "PATIENT_NOTES_NOT_FOUND"
}
```

**401 Unauthorized**:
```json
{
  "error": "Invalid API key",
  "code": "UNAUTHORIZED"
}
```

**403 Forbidden**:
```json
{
  "error": "Insufficient permissions to access patient notes",
  "code": "FORBIDDEN"
}
```

---

## 6. Get Vital Signs

**Endpoint**: `PUT /queries/ShortQuery`  
**Purpose**: Retrieve patient vital signs using SQL query

**Note**: This endpoint uses PUT method (not GET) and requires a SQL query in the request body. BMI is calculated as: (Weight/Height²) × 703

### Request

```http
PUT /api/v1/queries/ShortQuery HTTP/1.1
Host: example.opendental.com
DeveloperKey: YOUR_DEVELOPER_KEY
CustomerKey: YOUR_CUSTOMER_KEY
Content-Type: application/json
Accept: application/json
```

### Request Body

```json
{
  "query": "SELECT DateTaken, Pulse, BP, Height, Weight FROM vitalsign WHERE PatNum = 12345 ORDER BY DateTaken DESC"
}
```

### Response (200 OK)

```json
{
  "results": [
    {
      "DateTaken": "2025-11-29",
      "Pulse": 72,
      "BP": "120/80",
      "Height": 70,
      "Weight": 180,
      "BMI": 25.8
    },
    {
      "DateTaken": "2025-05-15",
      "Pulse": 68,
      "BP": "118/78",
      "Height": 70,
      "Weight": 175,
      "BMI": 25.1
    }
  ]
}
```

### Field Descriptions

- `DateTaken`: Date vital signs were recorded
- `Pulse`: Heart rate in beats per minute
- `BP`: Blood pressure (systolic/diastolic)
- `Height`: Height in inches
- `Weight`: Weight in pounds
- `BMI`: Body Mass Index (calculated as (Weight/Height²) × 703)

### Error Responses

**400 Bad Request**:
```json
{
  "error": "Invalid SQL query",
  "code": "BAD_REQUEST"
}
```

**401 Unauthorized**:
```json
{
  "error": "Invalid API key",
  "code": "UNAUTHORIZED"
}
```

**403 Forbidden**:
```json
{
  "error": "Insufficient permissions to execute queries",
  "code": "FORBIDDEN"
}
```

---

## Common Error Responses

All endpoints may return the following error statuses:

### 400 Bad Request
```json
{
  "error": "Invalid parameter format",
  "code": "BAD_REQUEST",
  "details": "PatNum must be a positive integer"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required",
  "code": "UNAUTHORIZED"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions",
  "code": "FORBIDDEN"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "code": "NOT_FOUND"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

**Header**: `Retry-After: 60` (seconds to wait)

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "code": "INTERNAL_ERROR"
}
```

### 503 Service Unavailable
```json
{
  "error": "Service temporarily unavailable",
  "code": "SERVICE_UNAVAILABLE",
  "retry_after": 120
}
```

---

## Timeout Specifications

Per Article III of constitution:

- **Connection timeout**: 10 seconds
- **Read timeout**: 30 seconds
- **Total request timeout**: 45 seconds

If any timeout is exceeded, treat as network error and apply retry logic.

---

## Retry Logic

Per Article III, retry the following:

**Retry eligible**:
- Network errors (no response received)
- 500 Internal Server Error
- 503 Service Unavailable
- Timeout errors

**Do NOT retry**:
- 400 Bad Request (client error)
- 401 Unauthorized (auth failure)
- 403 Forbidden (permission issue)
- 404 Not Found (resource doesn't exist)
- 422 Unprocessable Entity (validation error)

**Retry strategy**:
- Max attempts: 3
- Initial delay: 1 second
- Backoff multiplier: 2x (1s, 2s, 4s)
- Jitter: ±20% randomization

---

## Rate Limiting

OpenDental API rate limits (estimated):
- **Typical**: 100-1000 requests/hour per API key
- **Burst**: May allow higher rates for short periods

**Handling 429 responses**:
1. Extract `Retry-After` header value (seconds)
2. Wait specified duration
3. Display user message: "API rate limit reached, retrying in {seconds}s"
4. Retry request after wait period

---

## Testing Contracts

For each endpoint, create test fixtures in `tests/fixtures/`:

1. **Success case**: `{endpoint}_success.json`
2. **404 Not Found**: `{endpoint}_404.json`
3. **500 Server Error**: `{endpoint}_500.json`
4. **503 Unavailable**: `{endpoint}_503.json`
5. **Timeout**: Mock with `asyncio.TimeoutError`
6. **Malformed JSON**: `{endpoint}_malformed.json`

**Example fixture naming**:
- `patient_success.json`
- `patient_404.json`
- `appointment_500.json`
- `treatment_timeout.json` (simulated)

---

## Security Notes

1. **Never log raw responses**: May contain PHI
2. **Sanitize error messages**: Remove PatNum, AptNum from logged errors
3. **Certificate validation**: Always enabled (`verify=True`)
4. **TLS version**: Enforce TLS 1.2+ (HTTPX default)
5. **API key storage**: Keyring only, never in code or logs
