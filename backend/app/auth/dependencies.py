from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.dependencies import get_db
from app.models.user import User

# tokenUrl points at the login endpoint; used only for the /docs "Authorize"
# button, doesn't affect actual token validation.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid bearer token; raise 401 if missing/invalid."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_error

    email = decode_access_token(token)
    if email is None:
        raise credentials_error

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_error

    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Like get_current_user, but returns None instead of raising when there's
    no token. Used on endpoints (like /parking/recommend) that work for
    both anonymous and logged-in users, but personalize/log for the latter.
    """
    if token is None:
        return None

    email = decode_access_token(token)
    if email is None:
        return None

    return db.query(User).filter(User.email == email).first()


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require a valid token AND is_admin=True."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
