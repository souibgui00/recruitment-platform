import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, Boolean, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column
from cv_management.models import Base

class ApplicationMode(str, PyEnum):
    MANUAL_VALIDATION = "MANUAL_VALIDATION"
    FULL_AUTO = "FULL_AUTO"

class ApplicationStatus(str, PyEnum):
    PENDING_VALIDATION = "PENDING_VALIDATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"
    FAILED = "FAILED"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("match_id", name="uq_application_match"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    mode: Mapped[ApplicationMode] = mapped_column(Enum(ApplicationMode), default=ApplicationMode.MANUAL_VALIDATION)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING_VALIDATION)
    
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_logs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    screenshots: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def approve(self):
        if self.status != ApplicationStatus.PENDING_VALIDATION:
            raise ValueError(f"Cannot approve application in status: {self.status}")
        self.status = ApplicationStatus.APPROVED

    def reject(self, reason: Optional[str] = None):
        if self.status != ApplicationStatus.PENDING_VALIDATION:
            raise ValueError(f"Cannot reject application in status: {self.status}")
        self.status = ApplicationStatus.REJECTED
        self.failure_reason = reason

    def mark_as_sent(self):
        self.status = ApplicationStatus.SENT
        self.submitted_at = datetime.utcnow()
        self.failure_reason = None

    def mark_as_failed(self, reason: str):
        self.status = ApplicationStatus.FAILED
        self.failure_reason = reason

    def mark_as_manual_required(self, reason: str):
        self.status = ApplicationStatus.MANUAL_REQUIRED
        self.failure_reason = reason


class UserAutoApplySettings(Base):
    __tablename__ = "user_auto_apply_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    auto_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
