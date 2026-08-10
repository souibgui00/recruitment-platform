import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from job_sourcing.models import ContractType, OfferStatus, SourceType, RunStatus

class JobSourceBase(BaseModel):
    name: str
    type: SourceType
    base_url: str
    is_active: bool = True

class JobSourceCreate(JobSourceBase):
    pass

class JobSourceResponse(JobSourceBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class JobOfferResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    source_url: str
    title: str
    company: str
    location: Optional[str] = None
    description: str
    required_skills: Optional[str] = None
    contract_type: Optional[ContractType] = None
    posted_at: Optional[datetime] = None
    collected_at: datetime
    status: OfferStatus
    compatibility_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class CollectionRunResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    started_at: datetime
    finished_at: Optional[datetime] = None
    offers_collected: int
    status: RunStatus
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
