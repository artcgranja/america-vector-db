# src/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.core.config import settings
from contextlib import contextmanager

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()