import os
from pathlib import Path
import sys


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
)
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

APP_ROOT = Path(__file__).resolve().parent.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
