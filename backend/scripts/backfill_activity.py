"""
Backfill SYNTHETIC recent history so the forecast has a trend to show.

A freshly seeded database has no activity log, so the forecast (correctly)
says "not enough recent activity". For a demo you usually do not want to wait
half an hour for the simulator to build one up. This script invents it:

For every slot that is currently OCCUPIED it logs one "available -> occupied"
event at a random moment in the last N minutes. That keeps the log consistent
with the current state (each occupied slot did become occupied at some point)
and produces a realistic fill trend, steeper on floors that are fuller.

These rows are tagged source="backfill" so they are visible as synthetic in
the admin dashboard's activity feed. This is demo scaffolding, not data; do
not present it as real usage.

Usage (from the backend folder, venv active):
    python -m scripts.backfill_activity            # last 25 minutes
    python -m scripts.backfill_activity --minutes 20

Safe to re-run: it deletes its own previous rows first.
"""

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401,E402  (registers every model)
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.parking_slot import ParkingSlot  # noqa: E402
from app.models.slot_activity import SlotActivity  # noqa: E402

SOURCE = "backfill"


def backfill(minutes: int) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        removed = db.query(SlotActivity).filter(SlotActivity.source == SOURCE).delete()

        now = datetime.now(timezone.utc)
        occupied = db.query(ParkingSlot).filter(ParkingSlot.status == "occupied").all()

        per_floor: dict[tuple[int, int], int] = {}
        for index, slot in enumerate(occupied):
            # Spread events evenly through the window, with a little jitter.
            fraction = (index + random.random()) / max(len(occupied), 1)
            moment = now - timedelta(minutes=minutes * (1 - fraction) + 0.5)
            db.add(
                SlotActivity(
                    parking_slot_id=slot.id,
                    mall_id=slot.mall_id,
                    previous_status="available",
                    new_status="occupied",
                    source=SOURCE,
                    created_at=moment,
                )
            )
            key = (slot.mall_id, slot.floor)
            per_floor[key] = per_floor.get(key, 0) + 1

        db.commit()
        print(f"Removed {removed} old backfill rows, added {len(occupied)} new ones.")
        for (mall_id, floor), count in sorted(per_floor.items()):
            print(f"  mall {mall_id} floor {floor}: {count} fills over the last {minutes} min")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--minutes", type=int, default=25, help="how far back to spread events")
    args = parser.parse_args()
    if not 5 <= args.minutes <= 29:
        parser.error("--minutes must be between 5 and 29 (the forecast looks back 30)")
    backfill(args.minutes)
