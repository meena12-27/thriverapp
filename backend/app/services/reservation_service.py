"""
Shared reservation logic used by both the reservation routes and the
parking-availability routes (since an expired reservation must free up
its slot before availability is reported).
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.models.slot_activity import SlotActivity


def log_slot_activity(
    db: Session,
    *,
    slot,
    previous_status: str,
    new_status: str,
    source: str,
) -> None:
    db.add(
        SlotActivity(
            parking_slot_id=slot.id,
            mall_id=slot.mall_id,
            previous_status=previous_status,
            new_status=new_status,
            source=source,
        )
    )


def expire_stale_reservations(db: Session) -> None:
    """
    Flip any 'active' reservation whose hold time has passed to 'expired',
    and revert its slot back to 'available'. Called lazily at the top of
    any endpoint that reads/writes reservation or slot state, since there's
    no background scheduler in this app (see Reservation model docstring).
    """
    now = datetime.now(timezone.utc)

    stale = (
        db.query(Reservation)
        .filter(Reservation.status == "active", Reservation.expires_at < now)
        .all()
    )

    for reservation in stale:
        reservation.status = "expired"
        if reservation.parking_slot.status == "reserved":
            log_slot_activity(
                db,
                slot=reservation.parking_slot,
                previous_status="reserved",
                new_status="available",
                source="reservation",
            )
            reservation.parking_slot.status = "available"

    if stale:
        db.commit()
