# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 19:03:27 2026

@author: dimon
"""

from uuid import UUID


class VersionMismatchException(Exception):
    def __init__(self, feature_id: UUID, request_version: int, current_version: int, message: str):
        self.feature_id = feature_id
        self.request_version = request_version
        self.current_version = current_version
        self.message = message
