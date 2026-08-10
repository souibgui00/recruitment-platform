import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from cv_management.models import Base


class Match(Base):
    """
    Root aggregate for a computed match between a candidate CV and a Job Offer.
    Stores both the raw mathematical vector similarity and the LLM qualitative analysis.
    """
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("cv_id", "job_offer_id", name="uq_cv_job_offer_match"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cv_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), index=True)
    job_offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_offers.id", ondelete="CASCADE"), index=True)

    semantic_similarity: Mapped[float] = mapped_column(Float)  # Cosine similarity (0.0 to 1.0)
    llm_score: Mapped[float] = mapped_column(Float, default=0.0)  # Qualitative LLM score (0.0 to 100.0)
    compatibility_score: Mapped[float] = mapped_column(Float)  # Combined weighted score (0.0 to 100.0)

    matching_points: Mapped[Any] = mapped_column(JSON, default=list)  # Strengths / matching skills
    gap_points: Mapped[Any] = mapped_column(JSON, default=list)  # Missing skills / areas for growth
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Natural language explanation

    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MatchingConfig(Base):
    """
    Per-user matching preference configuration (weights & threshold).
    """
    __tablename__ = "matching_configs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    threshold: Mapped[float] = mapped_column(Float, default=70.0)  # Minimum score threshold for matching recommendations
    semantic_weight: Mapped[float] = mapped_column(Float, default=0.6)  # Weight of vector similarity (0.0 to 1.0)
    llm_weight: Mapped[float] = mapped_column(Float, default=0.4)  # Weight of LLM qualitative score (0.0 to 1.0)
