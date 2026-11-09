"""
Centralized configuration for Thriver backend.

Reads settings from environment variables (or a local .env file) instead
of hardcoding values like the database URL directly in source. This makes
it possible to run the same code against different databases (local dev,
Docker, CI, production) without editing code.
"""

import os
from functools import lru_cache

try:
    # Optional: if python-dotenv is installed, load a local .env file
    # automatically. This is not required in production, where real
    # environment variables are set by the platform (Docker, cloud host, etc).
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


_INSECURE_SECRET_KEY = "dev-only-insecure-secret-key"
_INSECURE_ADMIN_SECRET = "thriver-admin"


def _normalize_database_url(url: str) -> str:
    """Hosts like Render and Heroku hand out `postgres://...`, which
    SQLAlchemy 2 no longer accepts. Rewrite it to `postgresql://`."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def _split_origins(raw: str) -> list[str]:
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


class Settings:
    """Application settings sourced from environment variables."""

    DATABASE_URL: str = _normalize_database_url(
        os.getenv("DATABASE_URL", "postgresql://localhost/thriver_db")
    )

    # Comma-separated list of allowed CORS origins. Defaults to "*" for
    # local development; set this explicitly in production.
    ALLOWED_ORIGINS: list[str] = _split_origins(os.getenv("ALLOWED_ORIGINS", "*"))

    APP_NAME: str = os.getenv("APP_NAME", "Thriver Backend")
    ENV: str = os.getenv("ENV", "development")

    # --- Auth ---
    # In production, SECRET_KEY MUST be set via env var to a long random
    # value (e.g. `openssl rand -hex 32`). The fallback here is only for
    # local development so the app doesn't crash with no .env file.
    SECRET_KEY: str = os.getenv("SECRET_KEY", _INSECURE_SECRET_KEY)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    # A registering user becomes an admin only if they supply this value as
    # `admin_secret`. Keeps the demo simple (no separate admin-invite flow)
    # while not letting anyone self-promote by default.
    ADMIN_SIGNUP_SECRET: str = os.getenv("ADMIN_SIGNUP_SECRET", _INSECURE_ADMIN_SECRET)

    def validate_for_production(self) -> None:
        """Refuse to start in production with development defaults. A
        deployed app that signs tokens with a published key is worse than
        one that fails loudly at boot."""
        if self.ENV.lower() != "production":
            return
        problems = []
        if self.SECRET_KEY == _INSECURE_SECRET_KEY or len(self.SECRET_KEY) < 32:
            problems.append("SECRET_KEY must be set to a random value of 32+ characters")
        if self.ADMIN_SIGNUP_SECRET == _INSECURE_ADMIN_SECRET:
            problems.append("ADMIN_SIGNUP_SECRET must not be the default")
        if self.ALLOWED_ORIGINS == ["*"]:
            problems.append("ALLOWED_ORIGINS must list your real front-end origin(s), not *")
        if problems:
            raise RuntimeError("Unsafe production config: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so env vars are read once."""
    return Settings()
