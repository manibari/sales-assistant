"""Auth service — user management, password hashing, JWT."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from database.connection import get_connection

_SECRET = os.environ.get("JWT_SECRET", "nexus-dev-secret-change-in-prod")
_ALGORITHM = "HS256"
_EXPIRE_DAYS = 30


# ---------------------------------------------------------------------------
# Password helpers (bcrypt direct — passlib incompatible with bcrypt>=4)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_jwt(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_user_by_email(email: str) -> Optional[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, password_hash, role, is_active FROM nx_user WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "password_hash": row[3], "role": row[4], "is_active": row[5]}


def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, role, is_active, created_at FROM nx_user WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3], "is_active": row[4], "created_at": row[5]}


def list_users() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, role, is_active, created_at FROM nx_user ORDER BY id"
            )
            rows = cur.fetchall()
    return [
        {"id": r[0], "name": r[1], "email": r[2], "role": r[3], "is_active": r[4], "created_at": r[5]}
        for r in rows
    ]


def create_user(name: str, email: str, password: str, role: str = "manager") -> dict:
    hashed = hash_password(password)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_user (name, email, password_hash, role)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id, name, email, role, is_active, created_at""",
                (name, email, hashed, role),
            )
            row = cur.fetchone()
        conn.commit()
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3], "is_active": row[4], "created_at": row[5]}


def update_user(user_id: int, *, name: Optional[str] = None, role: Optional[str] = None,
                password: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[dict]:
    fields, vals = [], []
    if name is not None:
        fields.append("name = %s"); vals.append(name)
    if role is not None:
        fields.append("role = %s"); vals.append(role)
    if password is not None:
        fields.append("password_hash = %s"); vals.append(hash_password(password))
    if is_active is not None:
        fields.append("is_active = %s"); vals.append(is_active)
    if not fields:
        return get_user_by_id(user_id)
    fields.append("updated_at = NOW()")
    vals.append(user_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_user SET {', '.join(fields)} WHERE id = %s RETURNING id, name, email, role, is_active, created_at",
                vals,
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3], "is_active": row[4], "created_at": row[5]}
