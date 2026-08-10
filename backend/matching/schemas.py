import uuid
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, model_validator


class MatchAssessmentData(BaseModel):
    """
    Pydantic schema to validate the JSON structure returned by the LLM (Groq).
    """
    matching_points: List[str] = Field(default_factory=list, description="Strengths and matching skills")
    gap_points: List[str] = Field(default_factory=list, description="Missing skills or experience gaps")
    summary: str = Field(..., description="Short 1-2 sentence match justification")
    score: int = Field(..., ge=0, le=100, description="Overall compatibility score from 0 to 100")


class MatchResponse(BaseModel):
    """
    API Response schema for a Match object.
    """
    id: uuid.UUID
    cv_id: uuid.UUID
    job_offer_id: uuid.UUID

    semantic_similarity: float
    llm_score: float
    compatibility_score: float

    matching_points: List[str]
    gap_points: List[str]
    summary: Optional[str] = None
    computed_at: datetime

    # Optional nested details for list responses
    job_offer: Optional[Any] = None
    cv_info: Optional[Any] = None

    class Config:
        from_attributes = True


class MatchingConfigResponse(BaseModel):
    """
    API Response schema for MatchingConfig.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    threshold: float
    semantic_weight: float
    llm_weight: float

    class Config:
        from_attributes = True


class MatchingConfigUpdate(BaseModel):
    """
    Request payload to update MatchingConfig.
    """
    threshold: Optional[float] = Field(None, ge=0.0, le=100.0)
    semantic_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    llm_weight: Optional[float] = Field(None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weights(self):
        if self.semantic_weight is not None and self.llm_weight is not None:
            total = round(self.semantic_weight + self.llm_weight, 4)
            if total != 1.0:
                raise ValueError(f"The sum of semantic_weight ({self.semantic_weight}) and llm_weight ({self.llm_weight}) must equal 1.0")
        return self
