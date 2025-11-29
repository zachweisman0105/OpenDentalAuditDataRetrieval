"""Vital signs response model for OpenDental API."""

from pydantic import BaseModel, Field
from typing import Any


class VitalSignsResponse(BaseModel):
    """Patient vital signs.
    
    Matches OpenDental API PUT /queries/ShortQuery response schema.
    Contains vital sign information including Pulse, BP, Height, Weight.
    Note: BMI calculation needed: (Weight/Height^2)*703
    """
    
    # Generic container for vital signs data
    # The API returns query results
    data: list[dict[str, Any]] | dict[str, Any] = Field(
        default_factory=list,
        description="Vital signs data from API query"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "DateTaken": "2025-11-11T00:00:00",
                        "Pulse": 122,
                        "BP": "123/321",
                        "Height": 231.0,
                        "Weight": 98.0
                    }
                ]
            }
        }
    }
    
    def calculate_bmi(self, height: float, weight: float) -> float:
        """Calculate BMI from height and weight.
        
        Args:
            height: Height value
            weight: Weight value
            
        Returns:
            BMI value calculated as (Weight/Height^2)*703
        """
        if height <= 0:
            return 0.0
        return (weight / (height ** 2)) * 703
