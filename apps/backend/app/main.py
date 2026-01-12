# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 20:31:28 2025

@author: dimon
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.lifespan import lifespan
from api.auth import auth_router
from api.secure_router import secure_router
from api.layers import layers_router
from domain.exceptions.feature_not_found_exception import FeatureNotFoundException
from domain.exceptions.layer_not_found_exception import LayerNotFoundException
from domain.exceptions.unknown_storage_table_error import UnknownStorageTableError
from domain.exceptions.version_mismatch_exception import VersionMismatchException
from schemas.patch_feature_conflict_response import PatchFeatureConflictResponse
import os

app = FastAPI(lifespan=lifespan)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(secure_router)
app.include_router(layers_router)


@app.get("/health")
def health():
    return {"ok": True}


def install_exception_handlers(app: FastAPI):
    @app.exception_handler(FeatureNotFoundException)
    async def feature_not_found(_: Request, e: FeatureNotFoundException):
        return JSONResponse(status_code=404, content={"error": str(e)})

    @app.exception_handler(LayerNotFoundException)
    async def layer_not_found_exceptions(_: Request, e: LayerNotFoundException):
        return JSONResponse(status_code=404, content={"error": str(e)})

    @app.exception_handler(ValueError)
    async def value_error(_: Request, e: ValueError):
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


install_exception_handlers(app)
