from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Mall(Base):
    __tablename__ = "malls"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)

    parking_slots = relationship("ParkingSlot", back_populates="mall")