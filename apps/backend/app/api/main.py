# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 20:31:28 2025

@author: dimon
"""

import json
import uuid
from uuid import UUID
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from sqlalchemy import text, func, insert, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session, engine
from app.core.schemas.create_feature_point_request import CreateFeaturePointRequest
from app.core.schemas.create_feature_polygon_request import CreateFeaturePolygonRequest
from app.db.models import FeaturePoint, FeaturePolygon
from typing import Any
from pydantic import BaseModel


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
        geom_expr = geom_from_geojson(request.geometry)
        stmt = (
            insert(FeaturePoint)
            .values(id=uuid.uuid4(), geom=geom_expr, properties=request.properties)
            .returning(
                FeaturePoint.id,
                func.ST_AsGeoJSON(FeaturePoint.geom).label("geometry"),
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
            raise HTTPException(status_code=404, detail="Точка не найдена")
        return {
            "id": str(row.id),
            "geometry": json.loads(row.geometry),
            "properties": row.properties,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="БД не доступна") from e


@app.delete("/points/{id}")
async def delete_point(
    id: UUID, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    async with session.begin():
        stmt = (
            delete(FeaturePoint).where(FeaturePoint.id == id).returning(FeaturePoint.id)
        )
        res = await session.execute(stmt)
        row = res.one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Точка не найдена")
        return {"id": str(row.id)}


@app.put("/points/{id}")
async def update_point(
    id: UUID,
    request: CreateFeaturePointRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    async with session.begin():
        geom_expr = geom_from_geojson(request.geometry)
        stmt = (
            update(FeaturePoint)
            .values(geom=geom_expr, properties=request.properties)
            .where(FeaturePoint.id == id)
            .returning(
                FeaturePoint.id,
                func.ST_AsGeoJSON(FeaturePoint.geom).label("geometry"),
                FeaturePoint.properties,
            )
        )
        res = await session.execute(stmt)
        row = res.one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Точка не найдена")
        return {
            "id": str(row.id),
            "geometry": json.loads(row.geometry),
            "properties": row.properties,
        }


@app.post("/polygons")
async def add_polygon(
    request: CreateFeaturePolygonRequest, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    async with session.begin():
        geom_expr = geom_from_geojson(request.geometry)
        stmt = (
            insert(FeaturePolygon)
            .values(id=uuid.uuid4(), geom=geom_expr, properties=request.properties)
            .returning(
                FeaturePolygon.id,
                func.ST_AsGeoJSON(FeaturePolygon.geom).label("geometry"),
                FeaturePolygon.properties,
            )
        )
        res = await session.execute(stmt)
        row = res.one()
        return {
            "id": str(row.id),
            "geometry": json.loads(row.geometry),
            "properties": row.properties,
        }


@app.get("/polygons/{id}")
async def get_polygon(
    id: UUID, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    try:
        stmt = select(
            FeaturePolygon.id,
            func.ST_AsGeoJSON(FeaturePolygon.geom).label("geometry"),
            FeaturePolygon.properties,
        ).where(FeaturePolygon.id == id)
        res = await session.execute(stmt)
        row = res.one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Полигон не найден")
        return {
            "id": str(row.id),
            "geometry": json.loads(row.geometry),
            "properties": row.properties,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="БД недоступна") from e


@app.delete("/polygons/{id}")
async def delete_polygon(
    id: UUID, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    async with session.begin():
        stmt = (
            delete(FeaturePolygon)
            .where(FeaturePolygon.id == id)
            .returning(FeaturePolygon.id)
        )
        res = await session.execute(stmt)
        row = res.one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Полигон не найден")
        return {"id": str(row.id)}


@app.put("/polygons/{id}")
async def update_polygon(
    id: UUID,
    request: CreateFeaturePolygonRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    async with session.begin():
        geom_expr = geom_from_geojson(request.geometry)
        stmt = (
            update(FeaturePolygon)
            .where(FeaturePolygon.id == id)
            .values(geom=geom_expr, properties=request.properties)
            .returning(
                FeaturePolygon.id,
                func.ST_AsGeoJSON(FeaturePolygon.geom).label("geometry"),
                FeaturePolygon.properties,
            )
        )
        res = await session.execute(stmt)
        row = res.one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Полигон не найден")
        return {
            "id": str(row.id),
            "geometry": json.loads(row.geometry),
            "properties": row.properties,
        }


@app.post("/api/geojson/import")
async def upload_geojson(
    file: UploadFile = File(...), srid: int = Form(4326)
) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Имя файла пустое")
    if (not file.filename.lower().endswith(".geojson")) and (
        not file.filename.lower().endswith(".json")
    ):
        raise HTTPException(
            status_code=400, detail="Файл должен быть либо Geojson либо Json"
        )
    raw = await file.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Файл не является валидным GeoJson")

    typ = data.get("type")
    if typ not in ["Feature", "FeatureCollection"]:
        raise HTTPException(
            status_code=400,
            detail="Поле type Должно быть либо Feature либо FeatureCollection",
        )

    if typ == "FeatureCollection":
        features = data.get("features")
        if features is not list:
            raise HTTPException(
                status_code=400, detail="Поле features должно быть списком элементов"
            )
        if len(features) == 0:
            raise HTTPException(status_code=400, detail="Поле features пустой список")
    if typ == "Feature":
        geometry = data.get("geometry")
        if geometry is None:
            raise HTTPException(
                status_code=400, detail="Не корректная геометрия у Feature"
            )
        if geometry is not dict:
            raise HTTPException(
                status_code=400, detail="Некорректная геометрия у Feature"
            )
        geom_type = geometry.get("type")
        if geom_type is None or geom_type == "":
            raise HTTPException(status_code=400, detail="Тип геометрии не указан")
        coordinates = geometry.get("coordinates")
        if coordinates is None or coordinates == []:
            raise HTTPException(
                status_code=400, detail="Координаты геометрии не указаны"
            )

    result = {
        "status": "ok",
        "filename": file.filename,
        "rootType": data.get("type"),
        "srid": srid,
    }
    if typ == "FeatureCollection":
        result["count"] = len(features)
    else:
        result["count"] = 1

    return result


def geom_from_geojson(geometry: BaseModel, srid: int = 4326) -> Any:
    geojson_str = json.dumps(geometry.model_dump())
    geom_expr = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), srid)
    return geom_expr
