from __future__ import annotations
import uuid
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Index
from sqlalchemy import DateTime, func
from geoalchemy2 import Geometry
from .base import Base


class FeaturePoint(Base):
    __tablename__ = "feature_points"
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    """dataset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("datasets.id"), default=uuid.uuid4
    )
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)"""
    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


Index("ix_feature_points_geom_gist", FeaturePoint.geom, postgresql_using="gist")

"""class Dataset(Base):
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
    srid: Mapped[int] = mapped_column(nullable=False, default=4326)"""
