from pydantic import BaseModel, ConfigDict


class FloorForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    floor: int
    total_slots: int
    taken_now: int
    occupancy_now: float
    predicted_15m: float
    predicted_30m: float
    minutes_to_full: int | None
    trend: str  # filling | steady | emptying | unknown
    confidence: str  # low | medium | high
    events_used: int


class ForecastOut(BaseModel):
    mall_id: int
    method: str
    lookback_minutes: int
    floors: list[FloorForecastOut]
