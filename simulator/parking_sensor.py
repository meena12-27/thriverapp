"""
Fake parking sensors: every few seconds, flips one slot between
available and occupied, so the app has something changing to show.
Every change is logged to slot_activity, which powers the admin dashboard's
activity feed AND the occupancy forecast.

Reserved slots are deliberately left alone: a sensor would not know a slot is
reserved, and flipping it out from under an active reservation would be a
confusing demo bug.

--fill-bias controls the direction of travel:
    0.5  (default) arrivals and departures balance out: a steady lot
    0.8  a rush: most ticks fill a slot, so floors trend toward full and the
         forecast starts predicting it
    0.2  an exodus: floors trend toward empty

Usage (from the repo root, backend venv active):
    python simulator/parking_sensor.py
    python simulator/parking_sensor.py --fill-bias 0.8 --interval 3
"""

import argparse
import os
import random
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import app.models  # noqa: E402,F401  (registers every model before the first query)
from app.database import SessionLocal  # noqa: E402
from app.models.parking_slot import ParkingSlot  # noqa: E402
from app.services.reservation_service import log_slot_activity  # noqa: E402


def update_parking_status(fill_bias: float) -> None:
    db = SessionLocal()
    try:
        free = db.query(ParkingSlot).filter(ParkingSlot.status == "available").all()
        taken = db.query(ParkingSlot).filter(ParkingSlot.status == "occupied").all()

        want_fill = random.random() < fill_bias
        # If the preferred direction is impossible (nothing free to fill, or
        # nothing occupied to free), go the other way instead of idling.
        if want_fill and not free:
            want_fill = False
        elif not want_fill and not taken:
            want_fill = True

        pool = free if want_fill else taken
        if not pool:
            return

        slot = random.choice(pool)
        previous_status = slot.status
        new_status = "occupied" if want_fill else "available"

        log_slot_activity(
            db,
            slot=slot,
            previous_status=previous_status,
            new_status=new_status,
            source="simulator",
        )
        slot.status = new_status
        db.commit()

        print(
            f"[simulator] {slot.slot_number} (mall {slot.mall_id}, floor {slot.floor}): "
            f"{previous_status} -> {new_status}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--fill-bias", type=float, default=0.5,
                        help="probability a tick fills a slot instead of freeing one (0-1)")
    parser.add_argument("--interval", type=float, default=10,
                        help="seconds between ticks")
    args = parser.parse_args()
    if not 0 <= args.fill_bias <= 1:
        parser.error("--fill-bias must be between 0 and 1")

    while True:
        update_parking_status(args.fill_bias)
        time.sleep(args.interval)
