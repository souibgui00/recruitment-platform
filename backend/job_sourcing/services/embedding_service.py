from sqlalchemy.orm import Session
from cv_management.adapters.e5_embedding_provider import E5EmbeddingProvider
from job_sourcing.models import JobOffer, JobOfferEmbedding

# Initialize singleton provider
_embedding_provider = E5EmbeddingProvider()

class JobEmbeddingService:
    @staticmethod
    def generate_embedding(offer: JobOffer, db: Session) -> JobOfferEmbedding:
        """Generate and persist vector embedding for a normalized JobOffer."""
        # Clean string representing the job offer for document indexing
        text_to_embed = f"{offer.title} - {offer.company}. {offer.description[:800]}"
        
        # Calculate vector using the lazy-loaded E5 embedding provider
        vector = _embedding_provider.embed(text_to_embed)
        
        embedding_record = JobOfferEmbedding(
            job_offer_id=offer.id,
            vector=vector,
            model_name="intfloat/multilingual-e5-large"
        )
        return embedding_record
