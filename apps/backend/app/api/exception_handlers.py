from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions.business_validation_exception import BusinessValidationException
from domain.exceptions.feature_not_found_exception import FeatureNotFoundException
from domain.exceptions.layer_not_found_exception import LayerNotFoundException
from domain.exceptions.unknown_storage_table_error import UnknownStorageTableError
from domain.exceptions.version_mismatch_exception import VersionMismatchException
from schemas.patch_feature_conflict_response import PatchFeatureConflictResponse


def install_exception_handlers(app: FastAPI) -> None:
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
