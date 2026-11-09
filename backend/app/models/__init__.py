"""
Importing any model pulls in all of them.

SQLAlchemy resolves relationships by class name (e.g. ParkingSlot refers to
"Mall"), so every model must be imported before the first query. Doing it
here means standalone scripts (the simulator, seed_data) work without having
to remember a full import list.
"""

from app.models.mall import Mall  # noqa: F401
from app.models.parking_slot import ParkingSlot  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.parking_history import ParkingHistory  # noqa: F401
from app.models.reservation import Reservation  # noqa: F401
from app.models.slot_activity import SlotActivity  # noqa: F401
