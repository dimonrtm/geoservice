from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EditVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    work_order_id: UUID = Field(serialization_alias="workOrderId")
    owner_user_id: UUID = Field(serialization_alias="ownerId")
    status: Literal["open"]
    base_network_revision: int = Field(serialization_alias="baseNetworkRevision")
    created_at: datetime = Field(serialization_alias="createdAt")
    last_opened_at: datetime = Field(serialization_alias="lastOpenedAt")
