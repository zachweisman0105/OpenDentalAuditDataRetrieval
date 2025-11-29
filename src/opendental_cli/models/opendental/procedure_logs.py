"""Procedure logs response model for OpenDental API."""

from pydantic import BaseModel, Field
from typing import Any


class ProcedureLogsResponse(BaseModel):
    """Procedure codes and logs.
    
    Matches OpenDental API GET /procedurelogs?AptNum={AptNum} response schema.
    Contains procedure code information including ProcCode, Descript, ProcFee, ProcStatus.
    """
    
    # Generic container for procedure log data
    # The API returns an array or dict structure
    data: list[dict[str, Any]] | dict[str, Any] = Field(
        default_factory=list,
        description="Procedure log data from API"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "ProcCode": "D0220",
                        "Descript": "intraoral - periapical first radiographic image",
                        "ProcFee": "31.00",
                        "ProcStatus": "TP"
                    }
                ]
            }
        }
    }
