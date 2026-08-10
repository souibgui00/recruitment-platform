import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


class PersonalInfoResponse(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    salary_expectation: str | None = None

    class Config:
        from_attributes = True


class ExperienceResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    start_date: date
    end_date: date | None = None
    description: str | None = None
    is_current: bool = False

    class Config:
        from_attributes = True


class EducationResponse(BaseModel):
    id: uuid.UUID
    degree: str
    institution: str
    field: str | None = None
    start_date: date
    end_date: date | None = None

    class Config:
        from_attributes = True


class SkillResponse(BaseModel):
    id: uuid.UUID
    canonical_name: str
    category: str

    class Config:
        from_attributes = True


class CVResponse(BaseModel):
    id: uuid.UUID
    filename: str | None = None
    status: str
    raw_file_url: str
    created_at: datetime | None = None
    parsed_at: datetime | None = None
    failure_reason: str | None = None

    # Nested parsed data (populated after status=PARSED)
    personal_info: PersonalInfoResponse | None = None
    experiences: List[ExperienceResponse] = []
    educations: List[EducationResponse] = []
    skills: List[SkillResponse] = []

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