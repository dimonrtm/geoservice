from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from utility_service.use_cases.deps import (
    get_edit_version_service,
    get_work_order_service,
    get_workspace_service,
)
from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.use_cases.schemas.edit_version import EditVersionOut, OpenEditVersionOut
from utility_service.use_cases.schemas.work_order import AssignedWorkOrdersOut
from utility_service.use_cases.schemas.workspace import WorkspaceOut
from utility_service.use_cases.services.edit_version_service import EditVersionService
from utility_service.use_cases.services.work_order_service import WorkOrderService
from utility_service.use_cases.services.workspace_service import WorkspaceService
from utility_service.web_api.api.auth import require_editor


work_orders_router = APIRouter(prefix="/api/v1/work-orders", tags=["work-orders"])


@work_orders_router.get(
    "/assigned-to-me",
    response_model=AssignedWorkOrdersOut,
)
async def list_assigned_to_me(
    user: AuthUserDTO = Depends(require_editor),
    work_order_service: WorkOrderService = Depends(get_work_order_service),
) -> AssignedWorkOrdersOut:
    return await work_order_service.list_assigned_to_editor(user.id)


@work_orders_router.post(
    "/{work_order_id}/edit-versions",
    response_model=OpenEditVersionOut,
    status_code=status.HTTP_201_CREATED,
)
async def open_edit_version(
    work_order_id: UUID,
    response: Response,
    user: AuthUserDTO = Depends(require_editor),
    edit_version_service: EditVersionService = Depends(get_edit_version_service),
) -> OpenEditVersionOut:
    result = await edit_version_service.open_for_work_order(work_order_id, user.id)
    if not result.created:
        response.status_code = status.HTTP_200_OK

    edit_version = result.edit_version
    status_value = getattr(edit_version.status, "value", edit_version.status)
    return OpenEditVersionOut(
        created=result.created,
        edit_version=EditVersionOut(
            id=edit_version.id,
            work_order_id=edit_version.work_order_id,
            owner_user_id=edit_version.owner_user_id,
            status=status_value,
            base_network_revision=edit_version.base_network_revision,
            created_at=edit_version.created_at,
            last_opened_at=edit_version.last_opened_at,
        ),
    )


@work_orders_router.get(
    "/{work_order_id}/edit-versions/{edit_version_id}/workspace",
    response_model=WorkspaceOut,
)
async def get_workspace(
    work_order_id: UUID,
    edit_version_id: UUID,
    user: AuthUserDTO = Depends(require_editor),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceOut:
    return await workspace_service.get_workspace(
        work_order_id=work_order_id,
        edit_version_id=edit_version_id,
        actor_id=user.id,
    )
