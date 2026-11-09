from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParkingSlotOut(BaseModel):
    """Shape of a ParkingSlot as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slot_number: str
    floor: int
    status: str
    zone: str
    x_coordinate: int
    y_coordinate: int
    is_accessible: bool
    is_ev_charging: bool
    mall_id: int


class ParkingMapSlot(BaseModel):
    """Lightweight slot shape used by the /parking/map endpoint."""

    id: int
    mall_id: int
    slot: str
    floor: int
    status: str
    zone: str
    x: int
    y: int
    is_accessible: bool
    is_ev_charging: bool


class RecommendedSlot(BaseModel):
    slot: str
    floor: int
    zone: str
    is_accessible: bool
    is_ev_charging: bool


class RecommendationOut(BaseModel):
    """Shape of a parking recommendation as returned by the API."""

    mall: str
    parking: RecommendedSlot
    distance: float
    navigation: list[str]
    reasons: list[str]
    message: str


class NoAvailabilityOut(BaseModel):
    """Returned when there is no available parking slot for a mall."""

    message: str


class ParkingHistoryOut(BaseModel):
    """A past recommendation, shown in a logged-in user's history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mall_id: int
    slot_number: str
    floor: int
    zone: str
    distance: float
    created_at: datetime
