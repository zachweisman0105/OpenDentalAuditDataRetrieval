"""Medications response model for OpenDental API."""

from pydantic import BaseModel, Field
from typing import Any


class MedicationsResponse(BaseModel):
    """Patient medications.
    
    Matches OpenDental API GET /medicationpats?PatNum={PatNum} response schema.
    Contains medication information including medName, PatNote.
    Note: Inactive medications are not returned by the API.
    """
    
    # Generic container for medication data
    # The API returns an array or dict structure
    data: list[dict[str, Any]] | dict[str, Any] = Field(
        default_factory=list,
        description="Medication data from API"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
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
            }
        }
    }
