from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.dependencies import get_db
from app.models.parking_slot import ParkingSlot
from app.models.reservation import RESERVATION_HOLD_MINUTES, Reservation
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationOut
from app.services.reservation_service import expire_stale_reservations, log_slot_activity

router = APIRouter(prefix="/reservations", tags=["reservations"])


def _with_seconds_remaining(reservation: Reservation) -> ReservationOut:
    out = ReservationOut.model_validate(reservation)
    now = datetime.now(timezone.utc)
    expires_at = reservation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    remaining = (expires_at - now).total_seconds()
    out.seconds_remaining = max(0, int(remaining))
    return out


@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expire_stale_reservations(db)

    slot = db.query(ParkingSlot).filter(ParkingSlot.id == payload.parking_slot_id).first()
    if slot is None:
        raise HTTPException(status_code=404, detail="Parking slot not found")

    if slot.status != "available":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slot {slot.slot_number} is not available (status: {slot.status})",
        )

    # A user can only hold one active reservation at a time — release
    # any existing one before creating a new hold.
    existing = (
        db.query(Reservation)
        .filter(Reservation.user_id == current_user.id, Reservation.status == "active")
        .first()
    )
    if existing is not None:
        existing.status = "released"
        if existing.parking_slot.status == "reserved":
            log_slot_activity(
                db,
                slot=existing.parking_slot,
                previous_status="reserved",
                new_status="available",
                source="reservation",
            )
            existing.parking_slot.status = "available"

    reservation = Reservation(user_id=current_user.id, parking_slot_id=slot.id)
    log_slot_activity(
        db, slot=slot, previous_status="available", new_status="reserved", source="reservation"
    )
    slot.status = "reserved"

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return _with_seconds_remaining(reservation)


@router.post("/{reservation_id}/release", response_model=ReservationOut)
def release_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expire_stale_reservations(db)

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your reservation")

    if reservation.status == "active":
        reservation.status = "released"
        if reservation.parking_slot.status == "reserved":
            log_slot_activity(
                db,
                slot=reservation.parking_slot,
                previous_status="reserved",
                new_status="available",
                source="reservation",
            )
            reservation.parking_slot.status = "available"
        db.commit()
        db.refresh(reservation)

    return _with_seconds_remaining(reservation)


@router.get("/active", response_model=ReservationOut | None)
def get_active_reservation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expire_stale_reservations(db)

    reservation = (
        db.query(Reservation)
        .filter(Reservation.user_id == current_user.id, Reservation.status == "active")
        .first()
    )
    if reservation is None:
        return None

    return _with_seconds_remaining(reservation)
