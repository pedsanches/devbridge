"""
Security utilities.

JWT token creation and verification for authentication.
Fernet encryption for sensitive data storage.
"""

from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode.
        expires_delta: Custom expiration time. Defaults to settings.JWT_EXPIRE_DAYS.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.JWT_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT string to decode.

    Returns:
        Decoded payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


# --- Fernet Encryption for Sensitive Data ---


def _get_fernet() -> Fernet:
    """Get Fernet instance using JWT secret as key base."""
    # Derive a 32-byte key from JWT secret (Fernet requires URL-safe base64 key)
    import base64
    import hashlib

    key = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt_token(plaintext: str) -> bytes:
    """
    Encrypt a sensitive token (e.g., GitHub PAT).

    Args:
        plaintext: The token string to encrypt.

    Returns:
        Encrypted bytes.
    """
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode())


def decrypt_token(encrypted: bytes) -> str:
    """
    Decrypt a previously encrypted token.

    Args:
        encrypted: The encrypted bytes.

    Returns:
        Decrypted token string.
    """
    fernet = _get_fernet()
    return fernet.decrypt(encrypted).decode()
