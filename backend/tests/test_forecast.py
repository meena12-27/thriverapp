"""
Unit tests for the occupancy forecast and its use in recommendations.

Pure functions over hand-built slots and events: no database, no server.

    python -m tests.test_forecast
    pytest tests
"""

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.services.forecast_service import FloorForecast, forecast_floors  # noqa: E402
from app.services.recommendation_service import recommend  # noqa: E402

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)


def slots_for(floor, total, taken):
    return [
        SimpleNamespace(floor=floor, status="occupied" if i < taken else "available")
        for i in range(total)
    ]


def ev(floor, minutes_ago, prev="available", new="occupied"):
    return SimpleNamespace(
        floor=floor,
        previous_status=prev,
        new_status=new,
        created_at=NOW - timedelta(minutes=minutes_ago),
    )


def fill_events(floor, minutes_list):
    return [ev(floor, m) for m in minutes_list]


def test_no_activity_means_unknown_not_a_guess():
    f = forecast_floors(slots_for(1, 10, 4), [], now=NOW)[1]
    assert f.trend == "unknown" and f.confidence == "low"
    assert f.predicted_15m == f.occupancy_now == 40.0
    assert f.minutes_to_full is None


def test_too_few_events_refuses_to_extrapolate():
    f = forecast_floors(slots_for(1, 10, 4), fill_events(1, [20, 10]), now=NOW)[1]
    assert f.trend == "unknown"
    assert f.predicted_30m == 40.0  # unchanged, not extrapolated


def test_filling_floor_exact_numbers():
    # 6 fills over a 30 minute span -> 0.2 slots/min.
    # 10 slots, 4 taken: +3 in 15 min = 70%, +6 in 30 min = 100% (clamped),
    # 6 free / 0.2 per min = 30 minutes to full.
    events = fill_events(1, [30, 25, 20, 15, 10, 5])
    f = forecast_floors(slots_for(1, 10, 4), events, now=NOW)[1]
    assert f.trend == "filling"
    assert f.rate_per_minute == 0.2
    assert f.predicted_15m == 70.0
    assert f.predicted_30m == 100.0
    assert f.minutes_to_full == 30
    assert f.confidence == "medium" and f.events_used == 6


def test_emptying_floor():
    events = [ev(1, m, prev="occupied", new="available") for m in (30, 25, 20, 15, 10, 5)]
    f = forecast_floors(slots_for(1, 10, 8), events, now=NOW)[1]
    assert f.trend == "emptying"
    assert f.predicted_15m == 50.0  # 8 - 3 = 5 of 10
    assert f.predicted_30m == 20.0  # 8 - 6 = 2 of 10
    assert f.minutes_to_full is None  # an emptying floor is not about to fill


def test_balanced_arrivals_and_departures_are_steady():
    events = fill_events(1, [28, 20, 12]) + [
        ev(1, m, prev="occupied", new="available") for m in (24, 16, 8)
    ]
    f = forecast_floors(slots_for(1, 10, 5), events, now=NOW)[1]
    assert f.trend == "steady"
    assert f.predicted_30m == 50.0


def test_occupied_reserved_swaps_do_not_count():
    events = [ev(1, m, prev="occupied", new="reserved") for m in (20, 15, 10, 5)]
    f = forecast_floors(slots_for(1, 10, 4), events, now=NOW)[1]
    assert f.events_used == 0 and f.trend == "unknown"


def test_reservations_do_count_as_filling():
    events = [ev(1, m, prev="available", new="reserved") for m in (20, 15, 10, 5)]
    f = forecast_floors(slots_for(1, 10, 4), events, now=NOW)[1]
    assert f.events_used == 4 and f.trend == "filling"


def test_events_older_than_the_lookback_are_ignored():
    events = fill_events(1, [90, 80, 70, 60, 50, 40])
    f = forecast_floors(slots_for(1, 10, 4), events, now=NOW)[1]
    assert f.events_used == 0 and f.trend == "unknown"


def test_naive_datetimes_from_sqlite_are_treated_as_utc():
    events = fill_events(1, [20, 10, 5])
    for e in events:
        e.created_at = e.created_at.replace(tzinfo=None)
    f = forecast_floors(slots_for(1, 10, 4), events, now=NOW)[1]
    assert f.events_used == 3


def test_a_burst_cannot_produce_an_absurd_rate():
    # 3 fills inside the last minute: window is floored at 5 min, so the rate
    # is 3/5 = 0.6/min rather than 3 per minute.
    f = forecast_floors(slots_for(1, 100, 10), fill_events(1, [1, 0.5, 0.1]), now=NOW)[1]
    assert f.rate_per_minute == 0.6


def test_full_floor_reports_zero_minutes_and_stays_at_100():
    f = forecast_floors(slots_for(1, 4, 4), fill_events(1, [20, 10, 5]), now=NOW)[1]
    assert f.minutes_to_full == 0
    assert f.predicted_30m == 100.0


def test_far_off_fill_is_not_claimed():
    # 100 free slots at 0.1/min = 1000 minutes: not a credible prediction.
    f = forecast_floors(slots_for(1, 100, 0), fill_events(1, [30, 15, 5]), now=NOW)[1]
    assert f.trend == "filling" and f.minutes_to_full is None


def test_floors_are_forecast_independently():
    slots = slots_for(1, 10, 4) + slots_for(2, 10, 4)
    out = forecast_floors(slots, fill_events(1, [30, 25, 20, 15, 10, 5]), now=NOW)
    assert out[1].trend == "filling" and out[2].trend == "unknown"
    assert list(out) == [1, 2]


# ---- recommendations using forecasts -------------------------------------


def rslot(name, floor, x, y, status="available"):
    return SimpleNamespace(
        slot_number=name, floor=floor, x_coordinate=x, y_coordinate=y,
        status=status, is_accessible=False, is_ev_charging=False, zone="Z",
    )


def fc(floor, predicted_15m, minutes_to_full=None, occ=50.0):
    return FloorForecast(
        floor=floor, total_slots=2, taken_now=1, occupancy_now=occ,
        predicted_15m=predicted_15m, predicted_30m=predicted_15m,
        minutes_to_full=minutes_to_full, trend="filling", confidence="medium",
        events_used=5, rate_per_minute=0.2,
    )


def _two_floor_mall():
    # Floor 1: free slot at distance 10, one slot already taken (50% now).
    # Floor 2: free slot at distance 30, empty floor.
    return [
        rslot("f1_free", 1, 10, 0), rslot("f1_taken", 1, 10, 0, status="occupied"),
        rslot("f2_free", 2, 30, 0), rslot("f2_other", 2, 30, 0),
    ]


def test_without_forecast_the_closer_floor_wins():
    assert recommend(_two_floor_mall()).slot.slot_number == "f1_free"


def test_a_floor_about_to_fill_loses_to_a_quiet_one():
    # Now F1 is 50% (penalty 15 -> score 25 vs 30). Predicted to hit 100%
    # (penalty 30 -> score 40), so the quiet floor 2 wins.
    forecasts = {1: fc(1, 100.0, minutes_to_full=10), 2: fc(2, 0.0, occ=0.0)}
    best = recommend(_two_floor_mall(), forecasts=forecasts)
    assert best.slot.slot_number == "f2_free"
    assert "Floor 1 is predicted to fill in about 10 min" in best.reasons


def test_no_warning_about_the_floor_you_are_sent_to():
    forecasts = {1: fc(1, 100.0, minutes_to_full=10), 2: fc(2, 0.0, occ=0.0)}
    best = recommend(_two_floor_mall(), forecasts=forecasts)
    assert not any("Floor 2 is predicted" in r for r in best.reasons)


def test_no_warning_when_nothing_is_about_to_fill():
    forecasts = {1: fc(1, 50.0, minutes_to_full=None), 2: fc(2, 0.0, occ=0.0)}
    best = recommend(_two_floor_mall(), forecasts=forecasts)
    assert not any("predicted to fill" in r for r in best.reasons)


def test_a_far_off_fill_is_not_warned_about():
    forecasts = {1: fc(1, 60.0, minutes_to_full=90), 2: fc(2, 0.0, occ=0.0)}
    best = recommend(_two_floor_mall(), forecasts=forecasts)
    assert not any("predicted to fill" in r for r in best.reasons)


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("PASS", name)
        except AssertionError as exc:
            failed += 1
            print("FAIL", name, exc)
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
