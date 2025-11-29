"""Appointment response model for OpenDental API."""

from pydantic import BaseModel, Field


class AppointmentResponse(BaseModel):
    """Appointment scheduling and provider information.
    
    Matches OpenDental API GET /appointments/{AptNum} response schema.
    Contains PHI fields: AptDateTime, ProvName, Note.
    """
    
    AptNum: int = Field(description="Appointment number (primary key)")
    PatNum: int = Field(description="Patient number (foreign key)")
    AptDateTime: str = Field(description="Appointment date/time (ISO 8601)")
    AptStatus: str = Field(description="Appointment status (scheduled/complete/broken)")
    ProvNum: int = Field(description="Provider number")
    ProvName: str = Field(description="Provider name")
    ClinicNum: int = Field(description="Clinic number")
    Op: str = Field(default="", description="Operatory/room name")
    Pattern: str = Field(default="", description="Time pattern")
    Note: str = Field(default="", description="Appointment notes")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "AptNum": 67890,
                "PatNum": 12345,
                "AptDateTime": "2025-11-29T14:30:00Z",
                "AptStatus": "scheduled",
                "ProvNum": 5,
                "ProvName": "Dr. Sarah Smith",
                "ClinicNum": 1,
                "Op": "Op 3",
                "Pattern": "XXXX",
                "Note": "Regular checkup and cleaning"
            }
        }
    }
