from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkspaceAoiOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    description: str | None
    geometry: dict[str, Any]
    extent: list[float]
