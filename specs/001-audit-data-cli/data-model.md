# Data Model: OpenDental Audit Data Retrieval CLI

**Phase**: 1 - Design  
**Date**: 2025-11-29  
**Purpose**: Define Pydantic schemas for all entities in the system

## Overview

This document defines data models using Pydantic for type safety, validation, and serialization. All models follow constitution Article I (naming precision, single responsibility) and Article II (PHI handling requirements).

---

## Core Application Models

### AuditDataRequest

**Purpose**: Represents user's CLI invocation parameters

```python
from pydantic import BaseModel, Field, field_validator

class AuditDataRequest(BaseModel):
    """User request for audit data retrieval."""
    
    patnum: int = Field(gt=0, description="Patient Number (must be positive integer)")
    aptnum: int = Field(gt=0, description="Appointment Number (must be positive integer)")
    output_file: str | None = Field(None, description="Optional output file path")
    redact_phi: bool = Field(False, description="Whether to redact PHI in output")
    force_overwrite: bool = Field(False, description="Skip confirmation for existing output file")
    
    @field_validator('patnum', 'aptnum')
    @classmethod
    def validate_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("PatNum and AptNum must be positive integers")
        return v
```

**Validation Rules**:
- PatNum and AptNum must be > 0 (per spec edge cases)
- output_file validated separately for filesystem permissions
- redact_phi defaults to False (explicit opt-in for redaction)

---

### APICredential

**Purpose**: Represents OpenDental API authentication (stored in keyring)

```python
from pydantic import BaseModel, Field, HttpUrl, SecretStr

class APICredential(BaseModel):
    """OpenDental API credentials (NEVER log or display)."""
    
    base_url: HttpUrl = Field(description="OpenDental API base URL (e.g., https://server/api/v1)")
    api_key: SecretStr = Field(description="API key for Bearer authentication")
    environment: str = Field("production", description="Environment name (production, staging, dev)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "base_url": "https://example.opendental.com/api/v1",
                "api_key": "***REDACTED***",
                "environment": "production"
            }
        }
    }
    
    def get_auth_header(self) -> dict[str, str]:
        """Generate Authorization header (SecretStr ensures api_key not leaked in logs)."""
        return {"Authorization": f"Bearer {self.api_key.get_secret_value()}"}
```

**Security Notes**:
- `SecretStr` prevents accidental logging of API key
- `base_url` uses `HttpUrl` for validation (must be valid HTTPS URL)
- `get_auth_header()` encapsulates Bearer token format

---

### EndpointResponse

**Purpose**: Represents response from single API endpoint

```python
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

class EndpointResponse(BaseModel):
    """Response from a single OpenDental API endpoint."""
    
    endpoint_name: str = Field(description="Endpoint identifier (e.g., 'patient', 'appointment')")
    http_status: int = Field(description="HTTP status code (200, 404, 500, etc.)")
    success: bool = Field(description="Whether request succeeded")
    data: dict[str, Any] | None = Field(None, description="Parsed JSON response (None if failed)")
    error_message: str | None = Field(None, description="Error description (non-PHI)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp (UTC)")
    duration_ms: float = Field(description="Request duration in milliseconds")
    
    def is_retriable(self) -> bool:
        """Check if this failure should be retried (5xx or network error)."""
        return (not self.success) and (self.http_status >= 500 or self.http_status == 0)
```

**Usage**:
- `http_status=0` indicates network error (no response received)
- `error_message` must be sanitized (no PHI)
- `is_retriable()` implements Article III retry logic

---

### ConsolidatedAuditData

**Purpose**: Final output structure combining all endpoint responses

```python
from pydantic import BaseModel, Field
from typing import Dict

class ConsolidatedAuditData(BaseModel):
    """Consolidated audit data from multiple endpoints."""
    
    request: AuditDataRequest = Field(description="Original request parameters")
    success: Dict[str, dict] = Field(default_factory=dict, description="Successful endpoint responses")
    failures: list[Dict[str, str]] = Field(default_factory=list, description="Failed endpoint details")
    total_endpoints: int = Field(description="Total number of endpoints queried")
    successful_count: int = Field(description="Number of successful responses")
    failed_count: int = Field(description="Number of failed responses")
    retrieval_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data retrieval timestamp (UTC)")
    
    def exit_code(self) -> int:
        """Determine appropriate exit code: 0 (all success), 1 (all failed), 2 (partial)."""
        if self.failed_count == 0:
            return 0  # All success
        elif self.successful_count == 0:
            return 1  # All failed
        else:
            return 2  # Partial success
    
    def apply_phi_redaction(self) -> 'ConsolidatedAuditData':
        """Return new instance with PHI redacted in success data."""
        from ..phi_redactor import PHIRedactor  # Avoid circular import
        redactor = PHIRedactor()
        redacted_success = {
            endpoint: redactor.redact(data)
            for endpoint, data in self.success.items()
        }
        return self.model_copy(update={'success': redacted_success})
```

**Output Structure Example**:
```json
{
  "request": {"patnum": 12345, "aptnum": 67890, "redact_phi": false},
  "success": {
    "patient": {...},
    "appointment": {...},
    "treatment": {...}
  },
  "failures": [
    {"endpoint": "billing", "error": "Service unavailable (503)"}
  ],
  "total_endpoints": 6,
  "successful_count": 5,
  "failed_count": 1,
  "retrieval_timestamp": "2025-11-29T10:30:00Z"
}
```

---

### AuditLogEntry

**Purpose**: Single audit trail log record (NO PHI)

```python
from pydantic import BaseModel, Field
from datetime import datetime

class AuditLogEntry(BaseModel):
    """Audit log entry for compliance tracking (MUST NOT contain PHI)."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp (UTC)")
    operation_type: str = Field(description="Operation performed (e.g., 'fetch_patient', 'fetch_appointment')")
    endpoint: str = Field(description="API endpoint path (relative)")
    http_status: int = Field(description="HTTP status code")
    success: bool = Field(description="Whether operation succeeded")
    duration_ms: float = Field(description="Operation duration in milliseconds")
    error_category: str | None = Field(None, description="Error category if failed (non-PHI)")
    user_id: str = Field(description="System user running CLI (non-PHI, e.g., username)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2025-11-29T10:30:00Z",
                "operation_type": "fetch_patient",
                "endpoint": "/patients/REDACTED",
                "http_status": 200,
                "success": true,
                "duration_ms": 245.3,
                "error_category": null,
                "user_id": "system_user"
            }
        }
    }
```

**Critical**: PatNum, AptNum, patient names, DOB, SSN, dates MUST NOT appear in audit logs (Article II, Law 8)

---

## OpenDental API Response Models

### Base Class

```python
from pydantic import BaseModel, ConfigDict

class OpenDentalResponse(BaseModel):
    """Base class for all OpenDental API response models."""
    
    model_config = ConfigDict(
        extra='forbid',  # Reject unknown fields (detect API changes)
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    def redact_phi_fields(self) -> dict:
        """Override in subclasses to implement PHI redaction."""
        raise NotImplementedError("Subclasses must implement redact_phi_fields()")
```

---

### PatientResponse

```python
from datetime import date
from pydantic import Field
from typing import Optional

class PatientResponse(OpenDentalResponse):
    """Patient demographics from /patients/{PatNum} endpoint."""
    
    PatNum: int = Field(description="Patient Number (primary key)")
    FName: str = Field(description="First name (PHI)")
    LName: str = Field(description="Last name (PHI)")
    MiddleI: Optional[str] = Field(None, description="Middle initial")
    Birthdate: date = Field(description="Date of birth (PHI)")
    SSN: Optional[str] = Field(None, description="Social Security Number (PHI)")
    Gender: str = Field(description="Gender (M/F/Other)")
    Address: Optional[str] = Field(None, description="Street address (PHI)")
    City: Optional[str] = Field(None, description="City")
    State: Optional[str] = Field(None, description="State code")
    Zip: Optional[str] = Field(None, description="ZIP code")
    HmPhone: Optional[str] = Field(None, description="Home phone (PHI)")
    WkPhone: Optional[str] = Field(None, description="Work phone (PHI)")
    Email: Optional[str] = Field(None, description="Email address (PHI)")
    
    def redact_phi_fields(self) -> dict:
        """Redact PHI fields for --redact-phi flag."""
        data = self.model_dump()
        phi_fields = ['FName', 'LName', 'MiddleI', 'Birthdate', 'SSN', 'Address', 
                      'HmPhone', 'WkPhone', 'Email']
        for field in phi_fields:
            if data.get(field):
                data[field] = '[REDACTED]'
        return data
```

---

### AppointmentResponse

```python
from datetime import datetime
from pydantic import Field
from typing import Optional

class AppointmentResponse(OpenDentalResponse):
    """Appointment details from /appointments/{AptNum} endpoint."""
    
    AptNum: int = Field(description="Appointment Number (primary key)")
    PatNum: int = Field(description="Patient Number (foreign key)")
    AptDateTime: datetime = Field(description="Appointment date/time (PHI)")
    AptStatus: str = Field(description="Status (scheduled, complete, broken, etc.)")
    ProvNum: int = Field(description="Provider Number")
    ProvName: Optional[str] = Field(None, description="Provider name (PHI)")
    ClinicNum: Optional[int] = Field(None, description="Clinic identifier")
    Op: Optional[str] = Field(None, description="Operatory/room")
    Pattern: Optional[str] = Field(None, description="Time pattern")
    Note: Optional[str] = Field(None, description="Appointment note (may contain PHI)")
    
    def redact_phi_fields(self) -> dict:
        """Redact PHI fields."""
        data = self.model_dump()
        data['AptDateTime'] = '[REDACTED]'
        data['ProvName'] = '[REDACTED]'
        data['Note'] = '[REDACTED]'
        return data
```

---

### TreatmentResponse

```python
from datetime import date
from pydantic import Field
from typing import Optional, List

class ProcedureItem(BaseModel):
    """Single procedure/treatment item."""
    ProcNum: int
    ProcCode: str = Field(description="Procedure code (e.g., D0120)")
    ProcDate: date = Field(description="Date performed (PHI)")
    ProcFee: float = Field(description="Fee amount")
    ProcStatus: str = Field(description="Status (TP, C, EC, etc.)")
    ToothNum: Optional[str] = None
    Surf: Optional[str] = None
    Note: Optional[str] = None

class TreatmentResponse(OpenDentalResponse):
    """Treatment history from /procedures endpoint (filtered by PatNum)."""
    
    PatNum: int
    procedures: List[ProcedureItem] = Field(default_factory=list)
    
    def redact_phi_fields(self) -> dict:
        """Redact dates in procedures."""
        data = self.model_dump()
        for proc in data['procedures']:
            proc['ProcDate'] = '[REDACTED]'
            if proc.get('Note'):
                proc['Note'] = '[REDACTED]'
        return data
```

---

### BillingResponse

```python
from datetime import date
from pydantic import Field
from typing import List, Optional

class StatementItem(BaseModel):
    """Billing statement item."""
    StatementNum: int
    DateSent: date = Field(description="Statement date (PHI)")
    Balance: float
    IsSent: bool

class BillingResponse(OpenDentalResponse):
    """Billing records from /statements or /billing endpoint."""
    
    PatNum: int
    statements: List[StatementItem] = Field(default_factory=list)
    current_balance: float = Field(description="Current account balance")
    
    def redact_phi_fields(self) -> dict:
        """Redact dates."""
        data = self.model_dump()
        for stmt in data['statements']:
            stmt['DateSent'] = '[REDACTED]'
        return data
```

---

### InsuranceResponse

```python
from datetime import date
from pydantic import Field
from typing import List, Optional

class ClaimItem(BaseModel):
    """Insurance claim."""
    ClaimNum: int
    DateService: date = Field(description="Service date (PHI)")
    ClaimFee: float
    InsPayEst: float
    ClaimStatus: str

class InsuranceResponse(OpenDentalResponse):
    """Insurance claims from /claims endpoint."""
    
    PatNum: int
    claims: List[ClaimItem] = Field(default_factory=list)
    
    def redact_phi_fields(self) -> dict:
        """Redact service dates."""
        data = self.model_dump()
        for claim in data['claims']:
            claim['DateService'] = '[REDACTED]'
        return data
```

---

### ClinicalNotesResponse

```python
from datetime import datetime
from pydantic import Field
from typing import List

class ProgressNote(BaseModel):
    """Single clinical progress note."""
    ProgNoteNum: int
    NoteDateTime: datetime = Field(description="Note timestamp (PHI)")
    ProvNum: int
    Note: str = Field(description="Clinical note text (PHI)")

class ClinicalNotesResponse(OpenDentalResponse):
    """Clinical/progress notes from /progress_notes or /clinical_notes endpoint."""
    
    PatNum: int
    notes: List[ProgressNote] = Field(default_factory=list)
    
    def redact_phi_fields(self) -> dict:
        """Redact all note content and timestamps."""
        data = self.model_dump()
        for note in data['notes']:
            note['NoteDateTime'] = '[REDACTED]'
            note['Note'] = '[REDACTED]'
        return data
```

---

## Validation Rules Summary

| Model | Required Fields | Validation Rules | PHI Fields |
|-------|----------------|------------------|------------|
| AuditDataRequest | patnum, aptnum | Both > 0 | None |
| APICredential | base_url, api_key | HTTPS URL, non-empty key | api_key (SecretStr) |
| EndpointResponse | endpoint_name, http_status, success | status 0-599 | data (if contains PHI) |
| ConsolidatedAuditData | request, success, failures | counts consistent | success dict values |
| AuditLogEntry | All fields except error_category | NO PHI ALLOWED | None (by design) |
| PatientResponse | PatNum, FName, LName, Birthdate | PatNum > 0, valid date | FName, LName, Birthdate, SSN, Address, Phone, Email |
| AppointmentResponse | AptNum, PatNum, AptDateTime | AptNum/PatNum > 0 | AptDateTime, ProvName, Note |
| TreatmentResponse | PatNum, procedures | Valid dates | ProcDate, Note |
| BillingResponse | PatNum, statements | Valid amounts | DateSent |
| InsuranceResponse | PatNum, claims | Valid amounts | DateService |
| ClinicalNotesResponse | PatNum, notes | Valid timestamps | NoteDateTime, Note text |

---

## Relationships

```
AuditDataRequest
    ↓
ConsolidatedAuditData
    ├── success: Dict[str, OpenDentalResponse subclass]
    │   ├── "patient" → PatientResponse
    │   ├── "appointment" → AppointmentResponse
    │   ├── "treatment" → TreatmentResponse
    │   ├── "billing" → BillingResponse
    │   ├── "insurance" → InsuranceResponse
    │   └── "clinical_notes" → ClinicalNotesResponse
    └── failures: List[EndpointResponse]

APICredential → used by api_client.py

EndpointResponse → intermediate format before parsing to OpenDentalResponse

AuditLogEntry → written to audit.log (separate from ConsolidatedAuditData)
```

---

## Testing Considerations

Each model requires:
1. **Valid instantiation test**: All required fields populated
2. **Validation test**: Invalid data rejected (negative PatNum, invalid URL, etc.)
3. **PHI redaction test**: `redact_phi_fields()` replaces all PHI with `[REDACTED]`
4. **Serialization test**: `model_dump()` produces correct JSON structure
5. **Extra field rejection test**: Unknown fields trigger ValidationError

**Test coverage target**: 100% (these are data models, critical for data integrity)
