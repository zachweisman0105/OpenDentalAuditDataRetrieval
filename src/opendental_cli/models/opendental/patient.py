"""Patient response model for OpenDental API."""

from pydantic import BaseModel, Field


class PatientResponse(BaseModel):
    """Patient demographics and contact information.
    
    Matches OpenDental API GET /patients/{PatNum} response schema.
    Contains PHI fields: FName, LName, MiddleI, Birthdate, SSN, 
    Address, City, State, Zip, HmPhone, WkPhone, Email.
    """
    
    PatNum: int = Field(description="Patient number (primary key)")
    FName: str = Field(description="First name")
    LName: str = Field(description="Last name")
    MiddleI: str = Field(default="", description="Middle initial")
    Birthdate: str = Field(description="Date of birth (YYYY-MM-DD)")
    SSN: str = Field(default="", description="Social Security Number")
    Gender: str = Field(description="Gender (M/F/Other)")
    Address: str = Field(default="", description="Street address")
    City: str = Field(default="", description="City")
    State: str = Field(default="", description="State abbreviation")
    Zip: str = Field(default="", description="ZIP code")
    HmPhone: str = Field(default="", description="Home phone number")
    WkPhone: str = Field(default="", description="Work phone number")
    Email: str = Field(default="", description="Email address")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "PatNum": 12345,
                "FName": "John",
                "LName": "Doe",
                "MiddleI": "M",
                "Birthdate": "1985-03-15",
                "SSN": "123-45-6789",
                "Gender": "M",
                "Address": "123 Main St",
                "City": "Springfield",
                "State": "IL",
                "Zip": "62701",
                "HmPhone": "(555) 123-4567",
                "WkPhone": "(555) 987-6543",
                "Email": "john.doe@example.com"
            }
        }
    }
