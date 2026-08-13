import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from shared.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(50))
from enum import Enum as PyEnum
from sqlalchemy import Enum as SqlEnum

class CVStatus(str, PyEnum):
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    FAILED = "FAILED"

class CV(Base):
    __tablename__ = "cvs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    filename: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    raw_file_url: Mapped[str] = mapped_column(String(500))
    language: Mapped[str] = mapped_column(String(10))
    status: Mapped[CVStatus] = mapped_column(SqlEnum(CVStatus), default=CVStatus.UPLOADED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    def mark_as_parsed(self):
        self.status = CVStatus.PARSED
        self.parsed_at = datetime.utcnow()
        self.failure_reason = None

    def mark_as_failed(self, reason: str):
        self.status = CVStatus.FAILED
        self.failure_reason = reason

    def add_experience(self, title: str, company: str, start_date: date, end_date: Optional[date], description: Optional[str], is_current: bool):
        exp = Experience(
            cv_id=self.id,
            title=title,
            company=company,
            start_date=start_date,
            end_date=end_date,
            description=description,
            is_current=is_current
        )
        return exp

    def add_skill(self, skill_id: uuid.UUID, proficiency: str = "UNKNOWN", source: str = "EXPLICIT"):
        cv_skill = CVSkill(
            cv_id=self.id,
            skill_id=skill_id,
            proficiency=proficiency,
            source=source
        )
        return cv_skill

    def get_total_years_of_experience(self) -> float:
        # Simplistic approach if we were to compute it on the fly, but for now we'll just return 0.0 or compute from experiences if loaded
        return 0.0


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cv_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cvs.id"))
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)


class Education(Base):
    __tablename__ = "educations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cv_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cvs.id"))
    degree: Mapped[str] = mapped_column(String(200))
    institution: Mapped[str] = mapped_column(String(200))
    field: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cv_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cvs.id"))
    name: Mapped[str] = mapped_column(String(200))
    issuer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    date_obtained: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class PersonalInfo(Base):
    __tablename__ = "personal_infos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cv_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cvs.id"), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    salary_expectation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class CVEmbedding(Base):
    __tablename__ = "cv_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cv_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cvs.id"), unique=True)
    vector: Mapped[list[float]] = mapped_column(Vector(1024))
    model_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CVSkill(Base):
    __tablename__ = "cv_skills"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cv_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cvs.id"))
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    years_experience: Mapped[Optional[float]] = mapped_column(nullable=True)
    proficiency: Mapped[str] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(20))