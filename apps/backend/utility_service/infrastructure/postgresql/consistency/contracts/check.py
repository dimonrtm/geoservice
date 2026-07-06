from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

from sqlalchemy.sql.elements import TextClause


Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class CrossContextConsistencyCheck:
    name: str
    severity: Severity
    message: str
    source: str
    target: str | None
    sql: TextClause
    sample_fields: Mapping[str, str]
    sample_limit: int = 10

    def __post_init__(self) -> None:
        if self.sample_limit < 1:
            raise ValueError("sample_limit должен быть больше или равен 1")
