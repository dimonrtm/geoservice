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
from utility_service.utils.settings import settings

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(utility_network_router)
app.include_router(secure_router)
app.include_router(layers_router)
app.include_router(ws_layers_router)
app.include_router(work_orders_router)


@app.get("/health")
def health():
    return {"ok": True}


install_exception_handlers(app)
