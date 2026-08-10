from abc import ABC, abstractmethod
import uuid
from sqlalchemy.orm import Session


class IEmbeddingSimilarityCalculator(ABC):
    """
    Port interface for calculating semantic vector similarity between a CV and job offers.
    """

    @abstractmethod
    def calculate_single_similarity(self, cv_id: uuid.UUID, job_offer_id: uuid.UUID, db: Session) -> float:
        """
        Calculate raw cosine similarity (0.0 to 1.0) between a specific CV and JobOffer embedding.
        """
        ...

    @abstractmethod
    def get_top_matching_job_offers(self, cv_id: uuid.UUID, db: Session, limit: int = 20, threshold: float = 0.0) -> list[tuple[uuid.UUID, float]]:
        """
        Query vector similarity across all indexed job offers using pgvector <=> operator.
        Returns a list of tuples: (job_offer_id, cosine_similarity_score).
        """
        ...
