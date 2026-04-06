"""Auth router — login / logout / me / user management."""

from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

from services.nexus.auth import (
    create_jwt,
    create_user,
    decode_jwt,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user,
    verify_password,
)

router = APIRouter()

_COOKIE = "nexus_token"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


# ---------------------------------------------------------------------------
# Dependency helper (reusable in other routers)
# ---------------------------------------------------------------------------

def get_current_user(nexus_token: Optional[str] = Cookie(default=None)) -> dict:
    if not nexus_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_jwt(nexus_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(int(payload["sub"]))
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


def require_finance(current_user: dict = Depends(get_current_user)) -> dict:
    """Finance-equivalent: admin or user role."""
    if current_user["role"] not in ("admin", "user"):
        raise HTTPException(status_code=403, detail="Finance or admin only")
    return current_user


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "manager"


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    """Public self-registration — creates a 'manager' role account."""
    try:
        user = create_user(body.name, body.email, body.password, role="manager")
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="此電子郵件已被使用")
        raise
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}


@router.post("/login")
def login(body: LoginRequest, response: Response):
    user = get_user_by_email(body.email)
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    token = create_jwt(user["id"], user["role"])
    response.set_cookie(
        key=_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(nexus_token: Optional[str] = Cookie(default=None)):
    if not nexus_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_jwt(nexus_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(int(payload["sub"]))
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


@router.get("/users")
def list_all_users(_admin: dict = Depends(require_admin)):
    return list_users()


@router.post("/users", status_code=201)
def create_new_user(body: CreateUserRequest, _admin: dict = Depends(require_admin)):
    try:
        return create_user(body.name, body.email, body.password, body.role)
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email already exists")
        raise


@router.patch("/users/{user_id}")
def update_existing_user(user_id: int, body: UpdateUserRequest, _admin: dict = Depends(require_admin)):
    result = update_user(
        user_id,
        name=body.name,
        role=body.role,
        password=body.password,
        is_active=body.is_active,
    )
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result
