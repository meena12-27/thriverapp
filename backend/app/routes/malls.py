from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.mall import Mall
from app.schemas.mall import MallOut

router = APIRouter(prefix="/malls", tags=["malls"])


@router.get("", response_model=list[MallOut])
def get_malls(db: Session = Depends(get_db)):
    """Return every mall Thriver currently supports."""
    return db.query(Mall).all()
