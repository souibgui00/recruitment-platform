import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from enum import Enum as PyEnum
from sqlalchemy import Enum as SqlEnum

from shared.base import Base

class ContractType(str, PyEnum):
    CDI = "CDI"
    CDD = "CDD"
    STAGE = "STAGE"
    FREELANCE = "FREELANCE"

class OfferStatus(str, PyEnum):
    NEW = "NEW"
    ANALYZED = "ANALYZED"
    ARCHIVED = "ARCHIVED"

class SourceType(str, PyEnum):
    OFFICIAL_API = "OFFICIAL_API"
    SCRAPER = "SCRAPER"
    MOCK = "MOCK"

class RunStatus(str, PyEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"

class JobSource(Base):
    __tablename__ = "job_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[SourceType] = mapped_column(SqlEnum(SourceType))
    base_url: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class JobOffer(Base):
    __tablename__ = "job_offers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_sources.id"))
    source_url: Mapped[str] = mapped_column(String(1000), unique=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str] = mapped_column(String(300))
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    description: Mapped[str] = mapped_column(String) # unlimited length text
    required_skills: Mapped[Optional[str]] = mapped_column(String, nullable=True) # JSON serialized or comma separated
    contract_type: Mapped[Optional[ContractType]] = mapped_column(SqlEnum(ContractType), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[OfferStatus] = mapped_column(SqlEnum(OfferStatus), default=OfferStatus.NEW)

    def mark_as_analyzed(self):
        self.status = OfferStatus.ANALYZED

    def archive(self):
        self.status = OfferStatus.ARCHIVED

class JobOfferEmbedding(Base):
    __tablename__ = "job_offer_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_offers.id"), unique=True)
    vector: Mapped[list[float]] = mapped_column(Vector(1024))
    model_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_sources.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    offers_collected: Mapped[int] = mapped_column(default=0)
    status: Mapped[RunStatus] = mapped_column(SqlEnum(RunStatus))
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
