from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse

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
from utility_service.web_api.api.work_order_edit_route import WorkOrderEditRoute
from utility_service.web_api.api.geometry_save_contract import (
    EDIT_ERROR_RESPONSES,
    GEOMETRY_SAVE_REQUEST_SCHEMA,
)
from utility_service.web_api.parsers.geometry_save_request import parse_geometry_save_request
from utility_service.use_cases.schemas.edit_version.geometry_contract import GeometrySaveResponseOut


work_orders_router = APIRouter(prefix="/api/v1/work-orders", tags=["work-orders"])
work_order_edit_router = APIRouter(route_class=WorkOrderEditRoute)


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


@work_order_edit_router.get(
    "/{work_order_id}/edit-versions/{edit_version_id}/workspace",
    response_model=WorkspaceOut,
    responses=EDIT_ERROR_RESPONSES,
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


@work_order_edit_router.put(
    "/{work_order_id}/edit-versions/{edit_version_id}/features/{feature_id}/geometry",
    response_model=GeometrySaveResponseOut,
    responses=EDIT_ERROR_RESPONSES,
    description=(
        "Сохраняет геометрию или возвращает её к исходному состоянию. "
        "При повторе запроса возвращает результат первоначального сохранения. "
        "Актуальное состояние доступно при загрузке рабочего пространства. "
        "Если версия устарела, загрузите актуальное состояние перед новым сохранением."
    ),
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": GEOMETRY_SAVE_REQUEST_SCHEMA,
                },
            },
        },
    },
)
async def save_feature_geometry(
    work_order_id: UUID,
    edit_version_id: UUID,
    feature_id: UUID,
    request: Request,
    user: AuthUserDTO = Depends(require_editor),
    edit_version_service: EditVersionService = Depends(get_edit_version_service),
) -> JSONResponse:
    body = parse_geometry_save_request(await request.body())
    result = await edit_version_service.save_geometry(
        work_order_id=work_order_id,
        edit_version_id=edit_version_id,
        feature_id=feature_id,
        actor_id=user.id,
        request=body,
    )
    return JSONResponse(
        status_code=result.status_code,
        content=result.payload,
    )


work_orders_router.include_router(work_order_edit_router)
