"""Billing statement response model for OpenDental API."""

from pydantic import BaseModel, Field


class StatementRecord(BaseModel):
    """Individual billing statement record."""
    
    StatementNum: int = Field(description="Statement number (primary key)")
    DateSent: str = Field(description="Date statement sent (YYYY-MM-DD)")
    Balance: float = Field(description="Statement balance amount")
    IsSent: bool = Field(description="Whether statement was sent")


class BillingResponse(BaseModel):
    """Patient billing statements and account balance.
    
    Matches OpenDental API GET /statements?PatNum={PatNum} response schema.
    Contains minimal PHI: DateSent (financial date).
    """
    
    PatNum: int = Field(description="Patient number")
    statements: list[StatementRecord] = Field(
        default_factory=list,
        description="List of billing statements"
    )
    current_balance: float = Field(description="Current account balance")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "PatNum": 12345,
                "statements": [
                    {
                        "StatementNum": 501,
                        "DateSent": "2025-01-20",
                        "Balance": 245.00,
                        "IsSent": True
                    }
                ],
                "current_balance": 100.00
            }
        }
    }
