from __future__ import annotations
import uuid
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy import ForeignKey, String
from sqlalchemy import DateTime, func
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from .base import Base


class Feature(Base):
    __tablename__ = "features"
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("datasets.id"), default=uuid.uuid4
    )
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    geom: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="GEOMETRY", spatial_index=True), nullable=False
    )


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expected_geom_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="GEOMETRY"
    )
    srid: Mapped[int] = mapped_column(nullable=False, default=4326)
