"""Allergies response model for OpenDental API."""

from pydantic import BaseModel, Field
from typing import Any


class AllergiesResponse(BaseModel):
    """Patient allergies.
    
    Matches OpenDental API GET /allergies?PatNum={PatNum} response schema.
    Contains allergy information including defDescription, Reaction, StatusIsActive.
    """
    
    # Generic container for allergy data
    # The API returns an array or dict structure
    data: list[dict[str, Any]] | dict[str, Any] = Field(
        default_factory=list,
        description="Allergy data from API"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
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
            }
        }
    }
