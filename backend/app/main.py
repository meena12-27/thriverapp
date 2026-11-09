from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.models.mall import Mall
from app.models.parking_history import ParkingHistory
from app.models.parking_slot import ParkingSlot
from app.models.reservation import Reservation
from app.models.slot_activity import SlotActivity
from app.models.user import User
from app.routes import admin, auth, malls, parking, reservations

settings = get_settings()
settings.validate_for_production()

Base.metadata.create_all(bind=engine)


app = FastAPI(title=settings.APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parking.router)
app.include_router(malls.router)
app.include_router(auth.router)
app.include_router(reservations.router)
app.include_router(admin.router)

# Admin dashboard: a plain HTML/JS page (no build step) served at
# /admin-dashboard/. It talks to the same API using fetch() + the
# /auth/login and /admin/* endpoints above.
_static_dir = Path(__file__).parent / "static"
app.mount("/admin-dashboard", StaticFiles(directory=_static_dir / "admin", html=True), name="admin-dashboard")

@app.get("/health")
def health():
    """Liveness probe for Docker and the hosting platform."""
    return {"status": "ok"}


@app.get("/")
def home():
    return {
        "message": "Welcome to Thriver Backend"
    }