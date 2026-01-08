# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 21:03:39 2026

@author: dimon
"""

import uuid
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Integer, DateTime, text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry
from .base import Base


class FeatureLine(Base):
    __tablename__ = "feature_lines"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="LineString", srid=4326), nullable=False
    )
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"), default=1
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
