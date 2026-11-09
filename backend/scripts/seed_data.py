"""
Populate the database with demo malls and parking slots.

This didn't exist anywhere in the original project — whatever test data
was in the dev database before this was entered by hand, which is almost
certainly why switching malls in the app didn't look different: without a
script like this there's nothing enforcing that different malls actually
get different slot layouts.

Usage:
    cd backend
    python -m scripts.seed_data          # adds demo data (skips if already seeded)
    python -m scripts.seed_data --reset  # wipes and re-seeds
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine
from app.models.mall import Mall
from app.models.parking_history import ParkingHistory
from app.models.parking_slot import ParkingSlot
from app.models.reservation import Reservation
from app.models.slot_activity import SlotActivity

# Each mall gets a genuinely different layout: different slot counts,
# different floor counts, different coordinates, different starting
# occupancy — so two malls never look the same by coincidence.
MALLS = [
    {
        "name": "ABC Mall",
        "location": "Downtown",
        "floors": {
            1: {"zone": "A", "count": 6, "occupied": [0, 2]},
            2: {"zone": "B", "count": 6, "occupied": [1, 4, 5]},
        },
    },
    {
        "name": "Riverside Mall",
        "location": "Riverside District",
        "floors": {
            1: {"zone": "C", "count": 8, "occupied": [0, 1, 2, 3, 4, 5]},
            2: {"zone": "D", "count": 4, "occupied": []},
        },
    },
    {
        "name": "Skyline Plaza",
        "location": "Uptown",
        "floors": {
            1: {"zone": "E", "count": 5, "occupied": [3]},
        },
    },
]


def build_slots(floor: int, zone: str, count: int, occupied_indexes: list[int], mall_id: int):
    slots = []
    for i in range(count):
        col = i % 4
        row = i // 4
        slots.append(
            ParkingSlot(
                slot_number=f"{zone}{floor}{i + 1:02d}",
                floor=floor,
                zone=zone,
                status="occupied" if i in occupied_indexes else "available",
                # The Flutter map draws a slot at (x*8-20, y*6-20) inside a
                # 350px-high card with a driving lane at y~160-195, so these
                # values keep both rows below the lane and fully on screen.
                x_coordinate=6 + col * 9,
                y_coordinate=38 + row * 13,
                # First slot on each floor is accessible (nearest the lifts
                # in a real lot); last slot is an EV charging bay.
                is_accessible=(i == 0),
                is_ev_charging=(i == count - 1),
                mall_id=mall_id,
            )
        )
    return slots


def seed(reset: bool = False):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if reset:
            # Children first: PostgreSQL enforces the foreign keys (SQLite
            # does not), so slots can't be deleted while rows point at them.
            db.query(SlotActivity).delete()
            db.query(Reservation).delete()
            db.query(ParkingHistory).delete()
            db.query(ParkingSlot).delete()
            db.query(Mall).delete()
            db.commit()
        elif db.query(Mall).count() > 0:
            print("Malls already exist — skipping (use --reset to wipe and re-seed).")
            return

        for mall_data in MALLS:
            mall = Mall(name=mall_data["name"], location=mall_data["location"])
            db.add(mall)
            db.commit()
            db.refresh(mall)

            for floor, layout in mall_data["floors"].items():
                slots = build_slots(
                    floor=floor,
                    zone=layout["zone"],
                    count=layout["count"],
                    occupied_indexes=layout["occupied"],
                    mall_id=mall.id,
                )
                db.add_all(slots)

            db.commit()
            print(f"Seeded '{mall.name}' (id={mall.id})")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Wipe existing malls/slots first")
    args = parser.parse_args()
    seed(reset=args.reset)
