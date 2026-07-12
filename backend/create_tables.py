from sqlalchemy import text

from shared.database import engine
from cv_management.models import Base

with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    connection.commit()

Base.metadata.create_all(engine)

print("Tables créées avec succès.")