"""Insurance claim response model for OpenDental API."""

from pydantic import BaseModel, Field


class ClaimRecord(BaseModel):
    """Individual insurance claim record."""
    
    ClaimNum: int = Field(description="Claim number (primary key)")
    DateService: str = Field(description="Date of service (YYYY-MM-DD)")
    ClaimFee: float = Field(description="Total claim fee amount")
    InsPayEst: float = Field(description="Estimated insurance payment")
    ClaimStatus: str = Field(description="Claim status (Sent/Received/Processed)")


class InsuranceResponse(BaseModel):
    """Patient insurance claims.
    
    Matches OpenDental API GET /claims?PatNum={PatNum} response schema.
    Contains PHI fields: DateService (treatment date).
    """
    
    PatNum: int = Field(description="Patient number")
    claims: list[ClaimRecord] = Field(
        default_factory=list,
        description="List of insurance claims"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "PatNum": 12345,
                "claims": [
                    {
                        "ClaimNum": 701,
                        "DateService": "2025-01-15",
                        "ClaimFee": 245.00,
                        "InsPayEst": 195.00,
                        "ClaimStatus": "Sent"
                    }
                ]
            }
        }
    }
