from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

RESERVATION_HOLD_MINUTES = 5


class Reservation(Base):
    """
    A temporary hold on a parking slot. Status transitions:
      active   -> released  (user releases it, or reserves a different slot)
      active   -> expired   (hold time passed without being released/used)
    There's no background job expiring these; expiry is checked lazily
    (see expire_stale_reservations in routes/parking.py) whenever slot
    availability is read. That's a deliberate simplicity tradeoff for a
    single-instance demo app — a real deployment would use a scheduled
    job or a TTL-aware store instead.
    """

    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parking_slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)

    status = Column(String, default="active", nullable=False)  # active | released | expired

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=RESERVATION_HOLD_MINUTES),
    )

    user = relationship("User")
    parking_slot = relationship("ParkingSlot")
