from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class SlotActivity(Base):
    """
    A log of every status change a parking slot goes through — simulator
    toggles, reservations, releases, expiries. Powers the admin dashboard's
    "recent activity" feed and gives the busiest-zone stat something to
    look at beyond a single point-in-time snapshot.
    """

    __tablename__ = "slot_activity"

    id = Column(Integer, primary_key=True, index=True)
    parking_slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    mall_id = Column(Integer, ForeignKey("malls.id"), nullable=False)

    previous_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    source = Column(String, default="system")  # "simulator" | "reservation" | "system"

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    parking_slot = relationship("ParkingSlot")
    mall = relationship("Mall")
