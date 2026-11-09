from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ParkingHistory(Base):
    """
    One row per recommendation a logged-in user received. This is
    intentionally simple for now (Milestone 2) — it just logs what was
    recommended. Milestone 3 (Reservations) will extend this with actual
    hold/release state instead of a passive log.
    """

    __tablename__ = "parking_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mall_id = Column(Integer, ForeignKey("malls.id"), nullable=False)

    slot_number = Column(String, nullable=False)
    floor = Column(Integer, nullable=False)
    zone = Column(String, nullable=False)
    distance = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="history")
    mall = relationship("Mall")
