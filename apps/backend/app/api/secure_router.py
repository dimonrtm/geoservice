from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import get_current_user, require_editor

secure_router = APIRouter(prefix="/api/v1/secure", tags=["secure"])


@secure_router.get("/ping")
async def ping(user: dict = Depends(get_current_user)) -> dict:
    return {"status": "ok", "user_id": user["sub"], "role": user["role"]}


@secure_router.post("/ping")
async def ping_write(user: dict = Depends(require_editor)) -> dict:
    return {"status": "ok", "write": True, "user_id": user["sub"], "role": user["role"]}
