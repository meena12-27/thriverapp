"""
Shared FastAPI dependencies.

Previously get_db() was copy-pasted into every route file. Keeping a
single definition here means there's one place to change session
behavior (e.g. adding logging, retries) later.
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
