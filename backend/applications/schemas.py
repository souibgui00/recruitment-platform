import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from applications.models import ApplicationMode, ApplicationStatus

class ApplicationResponse(BaseModel):
    id: uuid.UUID
    match_id: uuid.UUID
    user_id: uuid.UUID
    mode: ApplicationMode
    status: ApplicationStatus
    submitted_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    cover_letter: Optional[str] = None
    execution_logs: Optional[Any] = None
    screenshots: Optional[Any] = None
    pending_question: Optional[Any] = None
    user_responses: Optional[Any] = None
    created_at: datetime
    
    # Nested info optionally populated in router/services
    match_details: Optional[Any] = None

    class Config:
        from_attributes = True

class UserAutoApplySettingsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    auto_apply_enabled: bool

    class Config:
        from_attributes = True

class UserAutoApplySettingsUpdate(BaseModel):
    auto_apply_enabled: bool
