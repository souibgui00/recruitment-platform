from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session

from job_sourcing.models import JobSource, CollectionRun, RunStatus
from job_sourcing.connectors.base import IJobConnector, get_connector
from job_sourcing.services.normalization_service import JobNormalizationService
from job_sourcing.services.deduplication_service import JobDeduplicationService
from job_sourcing.services.embedding_service import JobEmbeddingService

class JobCollectionService:
    @staticmethod
    def run_collection(source: JobSource, keywords: str, db: Session) -> CollectionRun:
        """Run the end-to-end collection, normalization, deduplication and embedding pipeline."""
        run = CollectionRun(
            source_id=source.id,
            status=RunStatus.SUCCESS, # Will be set to SUCCESS/FAILED at the end
            offers_collected=0,
            started_at=datetime.utcnow()
        )
        db.add(run)
        db.commit()
        
        try:
            connector = get_connector(source.name)
            if not connector.is_available():
                raise RuntimeError(f"Connector for {source.name} is currently unavailable.")
                
            raw_offers = connector.fetch_offers(source, keywords)
            
            new_offers_count = 0
            for raw_offer in raw_offers:
                # 1. Normalize raw DTO to JobOffer model
                offer = JobNormalizationService.normalize(raw_offer, source)
                
                # 2. Check for duplicate
                if JobDeduplicationService.is_duplicate(offer.fingerprint, db):
                    continue
                
                db.add(offer)
                db.flush() # Flush to assign database ID to the offer
                
                # 3. Generate embedding vector (optional — don't fail the whole collection if model crashes)
                try:
                    embedding = JobEmbeddingService.generate_embedding(offer, db)
                    db.add(embedding)
                except Exception as emb_err:
                    print(f"[Collection] Warning: embedding failed for offer '{offer.title}': {emb_err}")
                
                new_offers_count += 1
                
            run.offers_collected = new_offers_count
            run.finished_at = datetime.utcnow()
            run.status = RunStatus.SUCCESS
            db.commit()
            
        except Exception as e:
            db.rollback()
            # Reload run object after rollback and update its failure state
            db.add(run)
            run.finished_at = datetime.utcnow()
            run.status = RunStatus.FAILED
            run.error_message = str(e)
            db.commit()
            
        return run
