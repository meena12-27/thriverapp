from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_current_user_optional
from app.dependencies import get_db
from app.models.parking_history import ParkingHistory
from app.models.parking_slot import ParkingSlot
from app.models.user import User
from app.schemas.forecast import FloorForecastOut, ForecastOut
from app.schemas.parking import (
    NoAvailabilityOut,
    ParkingHistoryOut,
    ParkingMapSlot,
    ParkingSlotOut,
    RecommendationOut,
)
from app.services.forecast_service import (
    LOOKBACK_MINUTES,
    METHOD,
    get_mall_forecasts,
)
from app.services.recommendation_service import recommend
from app.services.reservation_service import expire_stale_reservations

router = APIRouter(prefix="/parking", tags=["parking"])


@router.get("/available", response_model=list[ParkingSlotOut])
def get_available_slots(
    mall_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """Return every currently-available slot for a given mall."""
    expire_stale_reservations(db)
    return (
        db.query(ParkingSlot)
        .filter(
            ParkingSlot.status == "available",
            ParkingSlot.mall_id == mall_id,
        )
        .all()
    )


@router.get("/recommend", response_model=RecommendationOut | NoAvailabilityOut)
def recommend_slot(
    mall_id: int = Query(1),
    entrance_x: int = Query(0, description="X position the user is starting from"),
    entrance_y: int = Query(0, description="Y position the user is starting from"),
    preferred_floor: int | None = Query(None, description="Prefer this floor if possible"),
    requires_accessible: bool = Query(False),
    requires_ev_charging: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Recommend the best available slot: distance from the user's entrance,
    current traffic on each floor, optional floor preference, and optional
    accessible / EV-charging requirements. Scoring lives in
    app/services/recommendation_service.py.

    If the request is authenticated, the result is also logged to the
    user's parking history.
    """
    expire_stale_reservations(db)

    all_slots = db.query(ParkingSlot).filter(ParkingSlot.mall_id == mall_id).all()
    forecasts = get_mall_forecasts(db, mall_id)

    best = recommend(
        all_slots,
        entrance_x=entrance_x,
        entrance_y=entrance_y,
        preferred_floor=preferred_floor,
        requires_accessible=requires_accessible,
        requires_ev_charging=requires_ev_charging,
        forecasts=forecasts,
    )

    if best is None:
        if requires_accessible or requires_ev_charging:
            return {"message": "No parking available matching your requirements"}
        return {"message": "No parking available"}

    chosen = best.slot

    if current_user is not None:
        # The app re-requests the recommendation every few seconds, so only
        # log it when it differs from the user's latest entry; otherwise the
        # history would fill with identical rows.
        latest = (
            db.query(ParkingHistory)
            .filter(ParkingHistory.user_id == current_user.id)
            .order_by(ParkingHistory.created_at.desc(), ParkingHistory.id.desc())
            .first()
        )
        is_repeat = (
            latest is not None
            and latest.mall_id == mall_id
            and latest.slot_number == chosen.slot_number
        )
        if not is_repeat:
            db.add(
                ParkingHistory(
                    user_id=current_user.id,
                    mall_id=mall_id,
                    slot_number=chosen.slot_number,
                    floor=chosen.floor,
                    zone=chosen.zone,
                    distance=best.distance,
                )
            )
            db.commit()

    return {
        "mall": chosen.mall.name,
        "parking": {
            "slot": chosen.slot_number,
            "floor": chosen.floor,
            "zone": chosen.zone,
            "is_accessible": chosen.is_accessible,
            "is_ev_charging": chosen.is_ev_charging,
        },
        "distance": best.distance,
        "navigation": [
            "Enter main entrance",
            f"Go to Floor {chosen.floor}",
            f"Park at Slot {chosen.slot_number}",
        ],
        "reasons": best.reasons,
        "message": f"Your recommended parking slot is {chosen.slot_number}",
    }


@router.get("/map", response_model=list[ParkingMapSlot])
def parking_map(
    mall_id: int = 1,
    db: Session = Depends(get_db),
):
    """Return every slot in a mall (available and occupied) for map rendering."""
    expire_stale_reservations(db)
    slots = db.query(ParkingSlot).filter(ParkingSlot.mall_id == mall_id).all()

    return [
        {
            "id": slot.id,
            "mall_id": slot.mall_id,
            "slot": slot.slot_number,
            "floor": slot.floor,
            "status": slot.status,
            "zone": slot.zone,
            "x": slot.x_coordinate,
            "y": slot.y_coordinate,
            "is_accessible": slot.is_accessible,
            "is_ev_charging": slot.is_ev_charging,
        }
        for slot in slots
    ]


@router.get("/forecast", response_model=ForecastOut)
def get_forecast(
    mall_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """
    Per-floor occupancy forecast for the next 15 and 30 minutes, plus an
    estimated time until each filling floor is full. This is a trend
    extrapolation over the last few minutes of slot activity, not a trained
    model; see app/services/forecast_service.py for exactly what it does and
    does not know.
    """
    expire_stale_reservations(db)
    forecasts = get_mall_forecasts(db, mall_id)
    return ForecastOut(
        mall_id=mall_id,
        method=METHOD,
        lookback_minutes=LOOKBACK_MINUTES,
        floors=[FloorForecastOut.model_validate(f) for f in forecasts.values()],
    )


@router.get("/history", response_model=list[ParkingHistoryOut])
def get_parking_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the logged-in user's past recommendations, most recent first."""
    return (
        db.query(ParkingHistory)
        .filter(ParkingHistory.user_id == current_user.id)
        .order_by(ParkingHistory.created_at.desc())
        .all()
    )
