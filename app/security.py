"""Password hashing and JWT access tokens."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, jwt_secret

# bcrypt silently truncates anything past 72 bytes, so we reject longer inputs
# in the schema layer instead of hashing a prefix.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    except ValueError:
        # Malformed hash in the database: treat as a failed login, not a 500.
        return False


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Return the user id encoded in the token, or None if it is not usable."""
    try:
        payload = jwt.decode(token, jwt_secret(), algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
