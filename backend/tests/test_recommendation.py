"""
Unit tests for the recommendation scoring engine.

The scoring function only reads attributes off slot objects, so these tests
use simple stand-in slots: no database, no web server.

Run from the backend folder, either way:
    python -m tests.test_recommendation
    pytest tests            (if you have pytest installed)
"""

import os
from types import SimpleNamespace

# The app module builds a database engine on import; SQLite in memory is
# enough for these tests, which never touch the database.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.services.recommendation_service import recommend  # noqa: E402


def slot(name, floor, x, y, status="available", accessible=False, ev=False):
    return SimpleNamespace(
        slot_number=name,
        floor=floor,
        x_coordinate=x,
        y_coordinate=y,
        status=status,
        is_accessible=accessible,
        is_ev_charging=ev,
        zone="Z",
    )


def test_nearest_wins_by_default():
    slots = [slot("far", 1, 50, 0), slot("near", 1, 5, 0)]
    assert recommend(slots).slot.slot_number == "near"


def test_entrance_position_changes_the_winner():
    slots = [slot("A", 1, 5, 0), slot("B", 1, 90, 0)]
    assert recommend(slots, entrance_x=0).slot.slot_number == "A"
    assert recommend(slots, entrance_x=100).slot.slot_number == "B"


def test_busy_floor_loses_to_emptier_floor():
    # Floor 1: 9 of 10 taken, free slot is closer (10) but pays ~27 traffic.
    # Floor 2: nearly empty, free slot is farther (25) but pays ~3 traffic.
    floor1 = [slot(f"f1_{i}", 1, 10, 0, status="occupied") for i in range(9)]
    floor1.append(slot("f1_free", 1, 10, 0))
    floor2 = [slot(f"f2_{i}", 2, 25, 0) for i in range(9)]
    floor2.append(slot("f2_occ", 2, 25, 0, status="occupied"))
    assert recommend(floor1 + floor2).slot.floor == 2


def test_no_traffic_gap_means_nearest_wins():
    slots = [slot("near", 1, 10, 0), slot("far", 1, 25, 0)]
    assert recommend(slots).slot.slot_number == "near"


def test_preferred_floor_is_a_soft_preference():
    modest = [slot("f1_close", 1, 10, 0), slot("f2_pref", 2, 20, 0)]
    assert recommend(modest, preferred_floor=2).slot.slot_number == "f2_pref"
    # ...but a much closer slot elsewhere still wins.
    big_gap = [slot("f1_close", 1, 5, 0), slot("f2_pref", 2, 80, 0)]
    assert recommend(big_gap, preferred_floor=2).slot.slot_number == "f1_close"


def test_accessible_is_a_hard_filter():
    slots = [slot("near_plain", 1, 1, 0), slot("far_acc", 1, 90, 0, accessible=True)]
    result = recommend(slots, requires_accessible=True)
    assert result.slot.slot_number == "far_acc"
    assert "Wheelchair accessible" in result.reasons


def test_ev_charging_is_a_hard_filter():
    slots = [slot("near_plain", 1, 1, 0), slot("far_ev", 1, 90, 0, ev=True)]
    assert recommend(slots, requires_ev_charging=True).slot.slot_number == "far_ev"


def test_returns_none_instead_of_a_wrong_slot():
    assert recommend([slot("a", 1, 1, 0)], requires_accessible=True) is None
    assert recommend([slot("a", 1, 1, 0, status="occupied")]) is None


def test_reserved_and_occupied_are_never_recommended():
    slots = [
        slot("reserved", 1, 1, 0, status="reserved"),
        slot("occupied", 1, 2, 0, status="occupied"),
        slot("ok", 1, 50, 0),
    ]
    assert recommend(slots).slot.slot_number == "ok"


def test_ties_are_stable():
    slots = [slot("first", 1, 10, 0), slot("second", 1, 10, 0)]
    assert recommend(slots).slot.slot_number == "first"


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("PASS", name)
        except AssertionError:
            failed += 1
            print("FAIL", name)
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
