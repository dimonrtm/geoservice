# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 23:31:46 2026

@author: dimon
"""

from uuid import UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String, Integer, text
from .base import Base


class Layer(Base):
    __tablename__ = "layers"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    geometry_type: Mapped[str] = mapped_column(String(200), nullable=False)
    srid: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("4326"), default=4326
    )
    storage_table: Mapped[str] = mapped_column(String(200), nullable=False)
