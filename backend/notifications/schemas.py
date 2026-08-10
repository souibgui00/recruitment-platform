import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from notifications.models import NotificationType

class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    message: str
    related_application_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
