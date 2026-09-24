from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db_config import DATABASE_URL, ENGINE_OPTIONS

engine = create_engine(DATABASE_URL, **ENGINE_OPTIONS)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()