from sqlalchemy import text

from shared.database import engine
from cv_management.models import Base
from user_management.models import User, UserSession, UserActivity
from job_sourcing.models import JobSource, JobOffer, JobOfferEmbedding, CollectionRun
from matching.models import Match, MatchingConfig
from applications.models import Application, UserAutoApplySettings
from notifications.models import Notification

with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    connection.commit()

Base.metadata.create_all(engine)

# Create HNSW index for vector similarity search
with engine.connect() as connection:
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_job_offer_embeddings_vector_hnsw
        ON job_offer_embeddings
        USING hnsw (vector vector_cosine_ops)
    """))
    connection.commit()

print("Tables créées avec succès.")