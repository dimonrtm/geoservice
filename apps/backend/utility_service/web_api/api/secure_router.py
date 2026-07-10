from __future__ import annotations

from fastapi import APIRouter, Depends

from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.web_api.api.auth import get_current_user, require_editor

secure_router = APIRouter(prefix="/api/v1/secure", tags=["secure"])


@secure_router.get("/ping")
async def ping(user: AuthUserDTO = Depends(get_current_user)) -> dict:
    return {"status": "ok", "user_id": str(user.id), "role": user.role}


@secure_router.post("/ping")
async def ping_write(user: AuthUserDTO = Depends(require_editor)) -> dict:
    return {
        "status": "ok",
        "write": True,
        "user_id": str(user.id),
        "role": user.role,
    }
