from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utility_service.web_api.api.lifespan import lifespan
from utility_service.web_api.api.auth import auth_router
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.secure_router import secure_router
from utility_service.web_api.api.utility_network import utility_network_router
from utility_service.web_api.api.layers import layers_router
from utility_service.web_api.api.ws_layers import ws_layers_router
from utility_service.web_api.api.work_orders import work_orders_router
from utility_service.web_api.middleware.correlation_id import (
    CORRELATION_ID_HEADER,
    CorrelationIdMiddleware,
)
from utility_service.utils.settings import settings

api = FastAPI(lifespan=lifespan)
api.add_middleware(CorrelationIdMiddleware)

api.include_router(auth_router)
api.include_router(utility_network_router)
api.include_router(secure_router)
api.include_router(layers_router)
api.include_router(ws_layers_router)
api.include_router(work_orders_router)


@api.get("/health")
def health():
    return {"ok": True}


install_exception_handlers(api)

app = CORSMiddleware(
    app=api,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=[CORRELATION_ID_HEADER],
)
