import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from ..database import get_connection
from ..schemas.auth import RegisterRequest


SECRET_KEY = os.environ.get("INTERNMATCH_SECRET_KEY", "internmatch-dev-secret")
ALGORITHM = "HS256"
TOKEN_LIFETIME_HOURS = 24


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    actual_salt = salt or os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), actual_salt, 100_000)
    return f"{actual_salt.hex()}:{derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, digest_hex = stored_hash.split(":")
    comparison = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(comparison, f"{salt_hex}:{digest_hex}")


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=TOKEN_LIFETIME_HOURS)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, object]:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def create_user(payload: RegisterRequest) -> dict[str, object]:
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (payload.email.lower(),),
        ).fetchone()
        if existing is not None:
            raise ValueError("An account with that email already exists.")

        cursor = connection.execute(
            """
            INSERT INTO users (full_name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload.full_name,
                payload.email.lower(),
                hash_password(payload.password),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        connection.commit()

    return get_user_by_id(cursor.lastrowid)


def authenticate_user(email: str, password: str) -> Optional[dict[str, object]]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, full_name, email, password_hash, created_at FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        return None

    return _serialize_user(row)


def get_user_by_id(user_id: int) -> Optional[dict[str, object]]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, full_name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return _serialize_user(row) if row is not None else None


def _serialize_user(row: object) -> dict[str, object]:
    return {
        "id": row["id"],
        "fullName": row["full_name"],
        "email": row["email"],
        "createdAt": row["created_at"],
    }
