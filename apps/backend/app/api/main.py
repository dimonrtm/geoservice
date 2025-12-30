# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 20:31:28 2025

@author: dimon
"""

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1;"))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail="DB is not reachable") from e
