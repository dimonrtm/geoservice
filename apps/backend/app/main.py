from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.lifespan import lifespan
from api.auth import auth_router
from api.exception_handlers import install_exception_handlers
from api.secure_router import secure_router
from api.layers import layers_router
from core.settings import settings

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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


install_exception_handlers(app)
