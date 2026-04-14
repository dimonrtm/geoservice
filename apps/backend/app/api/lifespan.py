# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 16:18:42 2026

@author: dimon
"""

from fastapi import FastAPI
from db.session import engine
from contextlib import asynccontextmanager
from services.realtime_connection_manager import WebSocketConnectionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.websocket_connection_manager = WebSocketConnectionManager()
    yield
    await engine.dispose()
