"""Treatment/procedure response model for OpenDental API."""

from pydantic import BaseModel, Field


class ProcedureRecord(BaseModel):
    """Individual procedure record."""
    
    ProcNum: int = Field(description="Procedure number (primary key)")
    ProcCode: str = Field(description="ADA procedure code")
    ProcDate: str = Field(description="Procedure date (YYYY-MM-DD)")
    ProcFee: float = Field(description="Procedure fee amount")
    ProcStatus: str = Field(description="Procedure status (C=Complete, TP=Treatment Plan)")
    ToothNum: str = Field(default="", description="Tooth number")
    Surf: str = Field(default="", description="Tooth surface")
    Note: str = Field(default="", description="Procedure notes")


class TreatmentResponse(BaseModel):
    """Patient treatment/procedure history.
    
    Matches OpenDental API GET /procedures?PatNum={PatNum} response schema.
    Contains PHI fields: ProcDate, ToothNum, Note (in procedure records).
    """
    
    PatNum: int = Field(description="Patient number")
    procedures: list[ProcedureRecord] = Field(
        default_factory=list,
        description="List of procedure records"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "PatNum": 12345,
                "procedures": [
                    {
                        "ProcNum": 101,
                        "ProcCode": "D0120",
                        "ProcDate": "2025-01-15",
                        "ProcFee": 150.00,
                        "ProcStatus": "C",
                        "ToothNum": "8",
                        "Surf": "",
                        "Note": "Periodic oral evaluation"
                    }
                ]
            }
        }
    }
