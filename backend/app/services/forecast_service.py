"""
Short-term occupancy forecast, per floor.

HOW IT WORKS (deliberately simple, and honest about it)
-------------------------------------------------------
This is trend extrapolation, not a trained model. For each floor we look at
the slot_activity log for the last LOOKBACK_MINUTES and count how many slots
became taken (occupied or reserved) minus how many became free. Dividing by
the time window gives a net fill rate in slots per minute. The forecast is
then:

    predicted taken = taken now + rate * minutes ahead   (clamped to the floor)

"Minutes until full" is the free slots divided by the rate, when the floor is
filling.

WHAT IT CANNOT DO
-----------------
It knows nothing about time of day, weekends, events or weather, and it
assumes the recent trend continues. With fewer than MIN_EVENTS_FOR_TREND
events in the window it refuses to guess (trend "unknown") instead of
extrapolating noise. A real model would learn weekly patterns from weeks of
history; this uses minutes. Same inputs, different ambition.

The functions here are pure (no database, no web), so they are unit tested
with hand-built slots and events. get_mall_forecasts() is the thin database
wrapper the routes use.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.models.parking_slot import ParkingSlot
from app.models.slot_activity import SlotActivity

METHOD = "recent trend extrapolation"

# How far back we look for a trend.
LOOKBACK_MINUTES = 30

# The rate is computed over the span the data actually covers, but never less
# than this, so two events a few seconds apart can't produce a huge rate.
MIN_WINDOW_MINUTES = 5

# Fewer net-changing events than this and we do not claim a trend at all.
MIN_EVENTS_FOR_TREND = 3
HIGH_CONFIDENCE_EVENTS = 10

# A "fill within N minutes" claim further out than this is not credible.
MAX_MINUTES_TO_FULL = 120

# A floor counts as filling/emptying if the 30 minute projection moves by at
# least this many slots.
TREND_THRESHOLD_SLOTS = 1.0


@dataclass
class FloorForecast:
    floor: int
    total_slots: int
    taken_now: int
    occupancy_now: float  # percent
    predicted_15m: float  # percent
    predicted_30m: float  # percent
    minutes_to_full: int | None
    trend: str  # "filling" | "steady" | "emptying" | "unknown"
    confidence: str  # "low" | "medium" | "high"
    events_used: int
    rate_per_minute: float  # net slots per minute, + means filling


def _aware(moment: datetime) -> datetime:
    """SQLite hands back naive datetimes; everything we store is UTC."""
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _is_taken(status: str) -> bool:
    return status != "available"


def forecast_floors(
    slots: list,
    events: list,
    now: datetime | None = None,
) -> dict[int, FloorForecast]:
    """
    slots:  objects with .floor and .status (every slot in one mall)
    events: objects with .floor, .previous_status, .new_status, .created_at
    Returns {floor: FloorForecast}, ordered by floor.
    """
    now = _aware(now) if now else datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=LOOKBACK_MINUTES)

    totals: dict[int, int] = {}
    taken: dict[int, int] = {}
    for slot in slots:
        totals[slot.floor] = totals.get(slot.floor, 0) + 1
        if _is_taken(slot.status):
            taken[slot.floor] = taken.get(slot.floor, 0) + 1

    # Only events that changed the taken count matter. occupied <-> reserved
    # does not change how many slots are free.
    deltas: dict[int, list[tuple[datetime, int]]] = {}
    for event in events:
        moment = _aware(event.created_at)
        if moment < cutoff or event.floor not in totals:
            continue
        was_taken = _is_taken(event.previous_status)
        now_taken = _is_taken(event.new_status)
        if was_taken == now_taken:
            continue
        deltas.setdefault(event.floor, []).append((moment, 1 if now_taken else -1))

    result: dict[int, FloorForecast] = {}

    for floor in sorted(totals):
        total = totals[floor]
        taken_now = taken.get(floor, 0)
        floor_events = deltas.get(floor, [])
        n = len(floor_events)

        has_trend = n >= MIN_EVENTS_FOR_TREND
        rate = 0.0
        if has_trend:
            span = (now - min(moment for moment, _ in floor_events)).total_seconds() / 60
            window = min(max(span, MIN_WINDOW_MINUTES), LOOKBACK_MINUTES)
            rate = sum(delta for _, delta in floor_events) / window

        def project(minutes: int) -> float:
            projected = min(max(taken_now + rate * minutes, 0.0), float(total))
            return round(projected / total * 100, 1)

        free = total - taken_now
        if free == 0:
            minutes_to_full: int | None = 0
        elif rate > 0:
            raw = free / rate
            minutes_to_full = (
                math.ceil(round(raw, 6)) if raw <= MAX_MINUTES_TO_FULL else None
            )
        else:
            minutes_to_full = None

        if not has_trend:
            trend = "unknown"
        elif rate * 30 >= TREND_THRESHOLD_SLOTS:
            trend = "filling"
        elif rate * 30 <= -TREND_THRESHOLD_SLOTS:
            trend = "emptying"
        else:
            trend = "steady"

        if n >= HIGH_CONFIDENCE_EVENTS:
            confidence = "high"
        elif has_trend:
            confidence = "medium"
        else:
            confidence = "low"

        result[floor] = FloorForecast(
            floor=floor,
            total_slots=total,
            taken_now=taken_now,
            occupancy_now=round(taken_now / total * 100, 1),
            predicted_15m=project(15),
            predicted_30m=project(30),
            minutes_to_full=minutes_to_full,
            trend=trend,
            confidence=confidence,
            events_used=n,
            rate_per_minute=round(rate, 4),
        )

    return result


def get_mall_forecasts(
    db: Session, mall_id: int, now: datetime | None = None
) -> dict[int, FloorForecast]:
    """Load one mall's slots and recent activity, then forecast each floor."""
    now = _aware(now) if now else datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=LOOKBACK_MINUTES)

    slots = db.query(ParkingSlot).filter(ParkingSlot.mall_id == mall_id).all()

    rows = (
        db.query(SlotActivity, ParkingSlot.floor)
        .join(ParkingSlot, ParkingSlot.id == SlotActivity.parking_slot_id)
        .filter(SlotActivity.mall_id == mall_id, SlotActivity.created_at >= cutoff)
        .all()
    )
    events = [
        SimpleNamespace(
            floor=floor,
            previous_status=activity.previous_status,
            new_status=activity.new_status,
            created_at=activity.created_at,
        )
        for activity, floor in rows
    ]

    return forecast_floors(slots, events, now=now)
