# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 20:31:28 2025

@author: dimon
"""

import json
import uuid
from uuid import UUID
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session, engine
from app.core.schemas.create_feature_point_request import CreateFeaturePointRequest
from app.db.models import FeaturePoint
from typing import Any


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


@app.post("/points")
async def add_point(
    request: CreateFeaturePointRequest, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    async with session.begin():
        geojson_str = json.dumps(request.geometry.model_dump())
        geom_expr = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326)

        stmt = (
            insert(FeaturePoint)
            .values(id=uuid.uuid4(), geom=geom_expr, properties=request.properties)
            .returning(
                FeaturePoint.id,
                func.ST_ASGeoJSON(FeaturePoint.geom).label("geometry"),
                FeaturePoint.properties,
            )
        )
        res = await session.execute(stmt)
        row = res.one()
        return {
            "id": str(row.id),
            "geometry": json.loads(row.geometry),
            "properties": row.properties,
        }


@app.get("/points/{id}")
async def get_point(
    id: UUID, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    try:
        stmt = select(
            FeaturePoint.id,
            func.ST_AsGeoJSON(FeaturePoint.geom).label("geometry"),
            FeaturePoint.properties,
        ).where(FeaturePoint.id == id)
        res = await session.execute(stmt)
        row = res.one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detal="Точка не найдена")
        return {
            "id": str(row.id),
            "geometry": json.loads(row.geometry),
            "properties": row.properties,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="БД не доступна") from e
