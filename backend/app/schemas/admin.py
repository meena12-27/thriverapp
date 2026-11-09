from datetime import datetime

from pydantic import BaseModel


class FloorStats(BaseModel):
    floor: int
    available: int
    occupied: int
    reserved: int
    total: int
    occupancy_percent: float


class ZoneStats(BaseModel):
    zone: str
    available: int
    occupied: int
    reserved: int
    total: int
    occupancy_percent: float


class MallStats(BaseModel):
    mall_id: int
    mall_name: str
    total_slots: int
    available: int
    occupied: int
    reserved: int
    occupancy_percent: float
    busiest_zone: str | None
    by_floor: list[FloorStats]
    by_zone: list[ZoneStats]


class ActivityEntryOut(BaseModel):
    slot_number: str
    floor: int
    zone: str
    previous_status: str
    new_status: str
    source: str
    created_at: datetime
