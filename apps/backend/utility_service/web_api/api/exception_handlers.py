from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from uuid import uuid4

from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.domain.exceptions.business_validation_exception import (
    BusinessValidationException,
)
from utility_service.use_cases.domain.exceptions.feature_not_found_exception import (
    FeatureNotFoundException,
)
from utility_service.use_cases.domain.exceptions.layer_not_found_exception import (
    LayerNotFoundException,
)
from utility_service.use_cases.domain.exceptions.unknown_storage_table_error import (
    UnknownStorageTableError,
)
from utility_service.use_cases.domain.exceptions.utility_network_api_error import (
    UtilityNetworkApiError,
)
from utility_service.use_cases.domain.exceptions.version_mismatch_exception import (
    VersionMismatchException,
)
from utility_service.use_cases.schemas.feature.patch_feature_conflict_response import (
    PatchFeatureConflictResponse,
)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthApiError)
    async def auth_api_error(request: Request, error: AuthApiError):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        return JSONResponse(
            status_code=error.status_code,
            content={
                "code": error.code,
                "message": error.message,
                "correlationId": correlation_id,
                "details": {},
            },
        )

    @app.exception_handler(UtilityNetworkApiError)
    async def utility_network_api_error(
        request: Request,
        error: UtilityNetworkApiError,
    ):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        return JSONResponse(
            status_code=error.status_code,
            content={
                "code": error.code,
                "message": error.message,
                "correlationId": correlation_id,
                "details": {},
            },
        )

    @app.exception_handler(FeatureNotFoundException)
    async def feature_not_found(_: Request, e: FeatureNotFoundException):
        return JSONResponse(status_code=404, content={"error": str(e)})

    @app.exception_handler(LayerNotFoundException)
    async def layer_not_found_exceptions(_: Request, e: LayerNotFoundException):
        return JSONResponse(status_code=404, content={"error": str(e)})

    @app.exception_handler(BusinessValidationException)
    async def business_validation_error(_: Request, e: BusinessValidationException):
        return JSONResponse(status_code=422, content={"error": str(e)})

    @app.exception_handler(UnknownStorageTableError)
    async def unknown_storage_table_error(_: Request, e: UnknownStorageTableError):
        return JSONResponse(status_code=422, content={"error": str(e)})

    @app.exception_handler(VersionMismatchException)
    async def version_mismatch_exception(_: Request, e: VersionMismatchException):
        patch_model = PatchFeatureConflictResponse(
            featureId=str(e.feature_id),
            requestVersion=e.request_version,
            currentVersion=e.current_version,
            message=e.message,
        )
        return JSONResponse(status_code=409, content=patch_model.model_dump())
