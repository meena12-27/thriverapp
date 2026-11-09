from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parking_slot_id: int
    status: str
    created_at: datetime
    expires_at: datetime
    seconds_remaining: int = 0


class ReservationCreate(BaseModel):
    parking_slot_id: int
