from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext


# ============================================================
# JWT CONFIGURATION
# ============================================================

SECRET_KEY = "smartlabel-ai-development-secret-change-this"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# ============================================================
# PASSWORD CONFIGURATION
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        password_hash,
    )


# ============================================================
# ACCESS TOKEN
# ============================================================

def create_access_token(
    user_id: int,
    email: str,
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ============================================================
# ACCESS TOKEN DECODING
# ============================================================

def decode_access_token(token: str):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return payload

    except JWTError:
        return None


# ============================================================
# PASSWORD RESET TOKEN
# ============================================================

PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 15


def create_password_reset_token():
    """
    Generate a cryptographically secure random token.

    The raw token is returned to the caller.
    Only its SHA-256 hash should be stored in the database.
    """

    raw_token = secrets.token_urlsafe(48)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = datetime.utcnow() + timedelta(
        minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )

    return raw_token, token_hash, expires_at


def hash_reset_token(token: str) -> str:
    """
    Convert a reset token into its SHA-256 hash.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()