from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String)
    floor = Column(Integer)
    status = Column(String)

    zone = Column(String)
    
    x_coordinate = Column(Integer)
    y_coordinate = Column(Integer)

    # Future-ready flags (Milestone 5): let the recommendation engine and
    # the map UI filter for these without another schema change later.
    is_accessible = Column(Boolean, default=False, nullable=False)
    is_ev_charging = Column(Boolean, default=False, nullable=False)

    mall_id = Column(Integer, ForeignKey("malls.id"))

    mall = relationship("Mall", back_populates="parking_slots")