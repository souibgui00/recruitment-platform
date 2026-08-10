import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session
from matching.ports.similarity_calculator import IEmbeddingSimilarityCalculator
from cv_management.models import CVEmbedding
from job_sourcing.models import JobOfferEmbedding


class PgVectorSimilarityCalculator(IEmbeddingSimilarityCalculator):
    """
    Adapter implementation using PostgreSQL pgvector <=> operator for cosine distance.
    Cosine Similarity = 1.0 - Cosine Distance.
    """

    def calculate_single_similarity(self, cv_id: uuid.UUID, job_offer_id: uuid.UUID, db: Session) -> float:
        cv_emb = db.query(CVEmbedding).filter_by(cv_id=cv_id).first()
        job_emb = db.query(JobOfferEmbedding).filter_by(job_offer_id=job_offer_id).first()

        if not cv_emb or not job_emb:
            raise ValueError(f"Missing vector embedding for CV {cv_id} or JobOffer {job_offer_id}")

        # Execute pgvector cosine distance calculation directly in PostgreSQL C engine
        query = text("""
            SELECT 1.0 - (c.vector <=> j.vector) AS similarity
            FROM cv_embeddings c, job_offer_embeddings j
            WHERE c.cv_id = :cv_id AND j.job_offer_id = :job_offer_id
        """)
        result = db.execute(query, {"cv_id": cv_id, "job_offer_id": job_offer_id}).fetchone()

        if not result or result[0] is None:
            return 0.0
        
        sim = float(result[0])
        # Bound similarity score between 0.0 and 1.0
        return max(0.0, min(1.0, sim))

    def get_top_matching_job_offers(self, cv_id: uuid.UUID, db: Session, limit: int = 20, threshold: float = 0.0) -> list[tuple[uuid.UUID, float]]:
        cv_emb = db.query(CVEmbedding).filter_by(cv_id=cv_id).first()
        if not cv_emb:
            raise ValueError(f"Missing vector embedding for CV {cv_id}")

        query = text("""
            SELECT j.job_offer_id, 1.0 - (c.vector <=> j.vector) AS similarity
            FROM cv_embeddings c, job_offer_embeddings j
            WHERE c.cv_id = :cv_id
            ORDER BY c.vector <=> j.vector ASC
            LIMIT :limit
        """)
        rows = db.execute(query, {"cv_id": cv_id, "limit": limit}).fetchall()

        results = []
        for row in rows:
            sim = float(row[1]) if row[1] is not None else 0.0
            sim = max(0.0, min(1.0, sim))
            if sim >= threshold:
                results.append((uuid.UUID(str(row[0])), sim))

        return results
