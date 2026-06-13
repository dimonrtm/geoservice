from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import get_current_user, require_editor
from models.user import User

secure_router = APIRouter(prefix="/api/v1/secure", tags=["secure"])


@secure_router.get("/ping")
async def ping(user: User = Depends(get_current_user)) -> dict:
    return {"status": "ok", "user_id": str(user.id), "role": user.role.value}


@secure_router.post("/ping")
async def ping_write(user: User = Depends(require_editor)) -> dict:
    return {
        "status": "ok",
        "write": True,
        "user_id": str(user.id),
        "role": user.role.value,
    }
