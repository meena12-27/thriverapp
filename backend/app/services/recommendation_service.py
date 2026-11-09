"""
Scoring logic for /parking/recommend.

The original version picked the slot closest to a hardcoded (0, 0) origin.
This version scores every available slot on:

  - walking distance from the entrance the caller specifies
  - how busy the slot's floor is right now (a proxy for traffic inside the
    parking lot: a nearly full floor means more circling to find the spot,
    even when the straight-line distance is short)
  - whether the slot is on the caller's preferred floor, if they gave one

When forecasts are supplied (see forecast_service.py) the traffic term uses
each floor's PREDICTED occupancy 15 minutes ahead instead of its current
occupancy, so a floor that is filling quickly is penalised before it is full.
That is what "proactive" means here: a trend-based heuristic, not a model.

Accessible and EV-charging needs are HARD filters, not score adjustments:
a driver who needs an accessible bay does not want a "closer but not
accessible" one.

Lower score wins. The weights are plain constants, not a trained model. Real
historical data comes in at the prediction milestone.
"""

import math
from dataclasses import dataclass

from app.models.parking_slot import ParkingSlot
from app.services.forecast_service import FloorForecast

# Slot coordinates in this app live roughly in 0-100, so a completely full
# floor (100% occupied) adds about 30 distance units of penalty: enough to
# matter, not enough to always override raw distance.
TRAFFIC_WEIGHT = 0.3

# Flat penalty (same units as distance) for a floor other than the preferred
# one. Soft on purpose: a much closer slot elsewhere can still win.
FLOOR_PREFERENCE_PENALTY = 25.0

# A floor predicted to fill within this many minutes is worth warning about.
FILL_WARNING_MINUTES = 30

# Below this floor occupancy we call a floor "low traffic" in the reasons.
LOW_TRAFFIC_THRESHOLD = 40.0


@dataclass
class ScoredSlot:
    slot: ParkingSlot
    distance: float
    score: float
    reasons: list[str]


def _distance(slot: ParkingSlot, x: int, y: int) -> float:
    return math.sqrt((slot.x_coordinate - x) ** 2 + (slot.y_coordinate - y) ** 2)


def floor_occupancy(all_slots: list[ParkingSlot]) -> dict[int, float]:
    """Occupancy percent per floor. Reserved counts as taken."""
    totals: dict[int, int] = {}
    taken: dict[int, int] = {}
    for slot in all_slots:
        totals[slot.floor] = totals.get(slot.floor, 0) + 1
        if slot.status != "available":
            taken[slot.floor] = taken.get(slot.floor, 0) + 1
    return {floor: (taken.get(floor, 0) / total) * 100 for floor, total in totals.items()}


def recommend(
    all_slots_in_mall: list[ParkingSlot],
    *,
    entrance_x: int = 0,
    entrance_y: int = 0,
    preferred_floor: int | None = None,
    requires_accessible: bool = False,
    requires_ev_charging: bool = False,
    forecasts: dict[int, FloorForecast] | None = None,
) -> ScoredSlot | None:
    """Return the best-scoring available slot, or None if nothing qualifies."""

    candidates = [s for s in all_slots_in_mall if s.status == "available"]

    if requires_accessible:
        candidates = [s for s in candidates if s.is_accessible]
    if requires_ev_charging:
        candidates = [s for s in candidates if s.is_ev_charging]

    if not candidates:
        return None

    # Occupancy is measured against the WHOLE mall, not just free slots, so it
    # reflects real congestion.
    occupancy_by_floor = floor_occupancy(all_slots_in_mall)

    nearest_raw = min(_distance(s, entrance_x, entrance_y) for s in candidates)

    best: ScoredSlot | None = None

    for slot in candidates:
        distance = _distance(slot, entrance_x, entrance_y)
        occupancy = occupancy_by_floor.get(slot.floor, 0.0)
        if forecasts and slot.floor in forecasts:
            occupancy = forecasts[slot.floor].predicted_15m

        traffic_penalty = occupancy * TRAFFIC_WEIGHT
        floor_penalty = (
            FLOOR_PREFERENCE_PENALTY
            if preferred_floor is not None and slot.floor != preferred_floor
            else 0.0
        )

        score = distance + traffic_penalty + floor_penalty

        reasons: list[str] = []
        if abs(distance - nearest_raw) < 0.01:
            reasons.append("Closest available slot")
        else:
            reasons.append("Best balance of distance and floor traffic")
        if occupancy < LOW_TRAFFIC_THRESHOLD:
            reasons.append("Low-traffic floor")
        if preferred_floor is not None and slot.floor == preferred_floor:
            reasons.append("On your preferred floor")
        if requires_accessible and slot.is_accessible:
            reasons.append("Wheelchair accessible")
        if requires_ev_charging and slot.is_ev_charging:
            reasons.append("EV charging available")

        candidate = ScoredSlot(
            slot=slot, distance=round(distance, 2), score=score, reasons=reasons
        )

        # Strict "<" keeps the first slot on ties, so results are stable
        # between polls instead of flickering between equal-scoring slots.
        if best is None or candidate.score < best.score:
            best = candidate

    if best is not None and forecasts:
        for floor, forecast in sorted(forecasts.items()):
            if (
                floor != best.slot.floor
                and forecast.minutes_to_full is not None
                and 0 < forecast.minutes_to_full <= FILL_WARNING_MINUTES
            ):
                best.reasons.append(
                    f"Floor {floor} is predicted to fill in about "
                    f"{forecast.minutes_to_full} min"
                )

    return best
