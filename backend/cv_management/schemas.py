import uuid
from datetime import datetime
from pydantic import BaseModel


class CVResponse(BaseModel):
    id: uuid.UUID
    status: str
    raw_file_url: str

    class Config:
        from_attributes = True