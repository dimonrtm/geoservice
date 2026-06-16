# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 16:18:42 2026

@author: dimon
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from utility_service.use_cases.deps import close_runtime_resources
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.websocket_connection_manager = WebSocketConnectionManager()
    yield
    await close_runtime_resources()
