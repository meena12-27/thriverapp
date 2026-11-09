from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin_user
from app.dependencies import get_db
from app.models.mall import Mall
from app.models.parking_slot import ParkingSlot
from app.models.slot_activity import SlotActivity
from app.models.user import User
from app.schemas.admin import ActivityEntryOut, FloorStats, MallStats, ZoneStats
from app.services.reservation_service import expire_stale_reservations

router = APIRouter(prefix="/admin", tags=["admin"])


def _occupancy_percent(occupied: int, reserved: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(((occupied + reserved) / total) * 100, 1)


@router.get("/stats", response_model=MallStats)
def get_mall_stats(
    mall_id: int = Query(1),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """
    Occupancy breakdown for a mall: totals, by floor, and by zone — the
    numbers a mall manager actually cares about (Milestone 4's "mall side"
    of the PRD).
    """
    expire_stale_reservations(db)

    mall = db.query(Mall).filter(Mall.id == mall_id).first()
    if mall is None:
        raise HTTPException(status_code=404, detail="Mall not found")

    slots = db.query(ParkingSlot).filter(ParkingSlot.mall_id == mall_id).all()

    total = len(slots)
    available = sum(1 for s in slots if s.status == "available")
    occupied = sum(1 for s in slots if s.status == "occupied")
    reserved = sum(1 for s in slots if s.status == "reserved")

    by_floor: dict[int, dict[str, int]] = {}
    by_zone: dict[str, dict[str, int]] = {}

    for slot in slots:
        floor_bucket = by_floor.setdefault(
            slot.floor, {"available": 0, "occupied": 0, "reserved": 0}
        )
        floor_bucket[slot.status] = floor_bucket.get(slot.status, 0) + 1

        zone_bucket = by_zone.setdefault(
            slot.zone, {"available": 0, "occupied": 0, "reserved": 0}
        )
        zone_bucket[slot.status] = zone_bucket.get(slot.status, 0) + 1

    floor_stats = [
        FloorStats(
            floor=floor,
            available=counts["available"],
            occupied=counts["occupied"],
            reserved=counts["reserved"],
            total=sum(counts.values()),
            occupancy_percent=_occupancy_percent(
                counts["occupied"], counts["reserved"], sum(counts.values())
            ),
        )
        for floor, counts in sorted(by_floor.items())
    ]

    zone_stats = [
        ZoneStats(
            zone=zone,
            available=counts["available"],
            occupied=counts["occupied"],
            reserved=counts["reserved"],
            total=sum(counts.values()),
            occupancy_percent=_occupancy_percent(
                counts["occupied"], counts["reserved"], sum(counts.values())
            ),
        )
        for zone, counts in by_zone.items()
    ]

    busiest_zone = max(zone_stats, key=lambda z: z.occupancy_percent, default=None)

    return MallStats(
        mall_id=mall.id,
        mall_name=mall.name,
        total_slots=total,
        available=available,
        occupied=occupied,
        reserved=reserved,
        occupancy_percent=_occupancy_percent(occupied, reserved, total),
        busiest_zone=busiest_zone.zone if busiest_zone else None,
        by_floor=floor_stats,
        by_zone=zone_stats,
    )


@router.get("/activity", response_model=list[ActivityEntryOut])
def get_recent_activity(
    mall_id: int = Query(1),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Most recent slot status changes for a mall — simulator + reservations."""
    entries = (
        db.query(SlotActivity)
        .filter(SlotActivity.mall_id == mall_id)
        .order_by(SlotActivity.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        ActivityEntryOut(
            slot_number=entry.parking_slot.slot_number,
            floor=entry.parking_slot.floor,
            zone=entry.parking_slot.zone,
            previous_status=entry.previous_status,
            new_status=entry.new_status,
            source=entry.source,
            created_at=entry.created_at,
        )
        for entry in entries
    ]
