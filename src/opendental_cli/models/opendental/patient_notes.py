"""Patient notes response model for OpenDental API."""

from pydantic import BaseModel, Field
from typing import Any


class PatientNotesResponse(BaseModel):
    """Patient medical notes.
    
    Matches OpenDental API GET /patientnotes/{PatNum} response schema.
    Contains medical information including MedicalComp (Medical History).
    Note: PatNum is required to be in the URL.
    """
    
    # Generic container for patient notes data
    # The API returns a dict structure
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Patient notes data from API"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": {
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
            }
        }
    }
