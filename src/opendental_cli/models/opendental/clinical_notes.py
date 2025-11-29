"""Clinical notes response model for OpenDental API."""

from pydantic import BaseModel, Field


class ProgressNoteRecord(BaseModel):
    """Individual progress note record."""
    
    ProgNoteNum: int = Field(description="Progress note number (primary key)")
    NoteDateTime: str = Field(description="Note timestamp (ISO 8601)")
    ProvNum: int = Field(description="Provider number")
    Note: str = Field(description="Clinical note text")


class ClinicalNotesResponse(BaseModel):
    """Clinical progress notes and documentation.
    
    Matches OpenDental API GET /progress_notes?PatNum={PatNum} response schema.
    Contains PHI fields: NoteDateTime, Note (clinical details).
    """
    
    PatNum: int = Field(description="Patient number")
    notes: list[ProgressNoteRecord] = Field(
        default_factory=list,
        description="List of progress notes"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "PatNum": 12345,
                "notes": [
                    {
                        "ProgNoteNum": 801,
                        "NoteDateTime": "2025-11-29T14:45:00Z",
                        "ProvNum": 5,
                        "Note": "Patient presented for scheduled cleaning. No issues."
                    }
                ]
            }
        }
    }
