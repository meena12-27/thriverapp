#!/bin/sh
set -e

# Wait until the database accepts connections (compose starts both at once).
python - << 'PY'
import sys, time
from sqlalchemy import create_engine, text
from app.config import get_settings

engine = create_engine(get_settings().DATABASE_URL)
for attempt in range(1, 31):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("database ready")
        break
    except Exception as exc:
        print(f"waiting for database ({attempt}/30): {exc.__class__.__name__}")
        time.sleep(2)
else:
    sys.exit("database never became reachable")
PY

# Create tables (app import does it) and seed the demo malls. The seed script
# skips itself when malls already exist, so restarts are safe.
python -m scripts.seed_data

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
