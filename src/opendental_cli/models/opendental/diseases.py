"""Diseases/problems response model for OpenDental API."""

from pydantic import BaseModel, Field
from typing import Any


class DiseasesResponse(BaseModel):
    """Patient diseases/problems.
    
    Matches OpenDental API GET /diseases?PatNum={PatNum} response schema.
    Contains disease/problem information including diseaseDefName, PatNote, ProbStatus.
    """
    
    # Generic container for disease data
    # The API returns an array or dict structure
    data: list[dict[str, Any]] | dict[str, Any] = Field(
        default_factory=list,
        description="Disease/problem data from API"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "DiseaseNum": 4811,
                        "PatNum": 39689,
                        "DiseaseDefNum": 92,
                        "diseaseDefName": "Anemic",
                        "PatNote": "dsasad",
                        "ProbStatus": "Active",
                        "DateStart": "0001-01-01",
                        "DateStop": "0001-01-01"
                    }
                ]
            }
        }
    }
