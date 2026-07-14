import uuid
from datetime import datetime
from pydantic import BaseModel


class CVResponse(BaseModel):
    id: uuid.UUID
    status: str
    raw_file_url: str

    class Config:
        from_attributes = True


class ExperienceData(BaseModel):
    title: str
    company: str
    start_date: str
    end_date: str | None = None
    description: str | None = None
    is_current: bool = False


class EducationData(BaseModel):
    degree: str
    institution: str
    field: str | None = None
    start_date: str
    end_date: str | None = None


class ParsedCVData(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    experiences: list[ExperienceData] = []
    education: list[EducationData] = []
    skills: list[str] = []