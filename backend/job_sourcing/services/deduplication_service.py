from sqlalchemy.orm import Session
from job_sourcing.models import JobOffer

class JobDeduplicationService:
    @staticmethod
    def is_duplicate(fingerprint: str, db: Session) -> bool:
        """Check if a job offer with the same fingerprint already exists in the database."""
        return db.query(JobOffer).filter(JobOffer.fingerprint == fingerprint).first() is not None
