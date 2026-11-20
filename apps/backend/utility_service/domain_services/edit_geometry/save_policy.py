"""Последовательность проверок первого изменения линии в рабочей версии."""

from dataclasses import dataclass, replace
from typing import Literal

from .structure import has_matching_structure, internal_vertex_indices, validate_transition
from .types import GeometryRuleError, GeometryValue, PreparedGeometry, TransitionResult


@dataclass(frozen=True)
class EditRejection:
    code: str
    reason: str

    @classmethod
    def invalid_context(cls, reason: str) -> "EditRejection":
        return cls("WORK_ORDER_CONTEXT_INVALID", reason)


@dataclass(frozen=True)
class NeedBaseline:
    def evaluate(self, geometry: GeometryValue) -> EditRejection | None:
        if geometry.type != "LineString":
            return EditRejection.invalid_context(
                "Геометрия базового состояния не соответствует типу объекта."
            )
        if len(geometry.coordinates) < 3:
            return EditRejection("FEATURE_NOT_EDITABLE", "У линии нет внутренней вершины.")
        return None


def begin_baseline(feature_type: str, operation: str | None) -> NeedBaseline | EditRejection:
    if feature_type != "line" or operation in ("created", "deleted"):
        return EditRejection(
            "FEATURE_NOT_EDITABLE", "Объект не поддерживает изменение геометрии линии."
        )
    return NeedBaseline()


def check_saved_line(
    baseline: GeometryValue, current: GeometryValue, operation: str | None
) -> EditRejection | None:
    if not has_matching_structure(baseline, current):
        return EditRejection.invalid_context(
            "Структура текущей геометрии отличается от базового состояния."
        )
    indices = internal_vertex_indices(baseline, current)
    if indices is None:
        return EditRejection.invalid_context(
            "Текущая геометрия нарушает правило изменения одной внутренней вершины."
        )
    if operation != ("updated" if indices else "unchanged"):
        return EditRejection.invalid_context(
            "Признак изменения объекта противоречит текущей геометрии."
        )
    return None


@dataclass(frozen=True)
class SpatialFacts:
    geometry_valid: bool
    aoi_valid: bool
    aoi_covered: bool


@dataclass(frozen=True)
class NeedCandidateSpatial:
    transition: TransitionResult

    def evaluate(self, facts: SpatialFacts) -> TransitionResult | EditRejection:
        if not facts.geometry_valid:
            return EditRejection("GEOMETRY_INVALID", "Предлагаемая геометрия недопустима.")
        if not facts.aoi_covered:
            return EditRejection(
                "GEOMETRY_OUTSIDE_AOI", "Предлагаемая геометрия выходит за пределы области работ."
            )
        return self.transition


@dataclass(frozen=True)
class NeedStoredSpatial:
    source: Literal["baseline", "current"]
    baseline: GeometryValue
    current: GeometryValue
    other_changed: bool
    prepared: PreparedGeometry

    def evaluate(
        self, facts: SpatialFacts
    ) -> "NeedStoredSpatial | NeedCandidateSpatial | EditRejection":
        if not (facts.geometry_valid and facts.aoi_valid and facts.aoi_covered):
            return EditRejection.invalid_context(
                "Исходная геометрия или область работ нарушает пространственные ограничения."
            )
        if self.source == "baseline":
            return replace(self, source="current")
        if self.other_changed:
            return EditRejection(
                "MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED", "В версии уже изменён другой объект."
            )
        try:
            transition = validate_transition(self.baseline, self.current, self.prepared)
        except GeometryRuleError as error:
            return EditRejection(error.code, "Предлагаемая геометрия нарушает правила изменения.")
        return NeedCandidateSpatial(transition)


@dataclass(frozen=True)
class NeedCurrent:
    baseline: GeometryValue
    operation: str | None
    other_changed: bool
    prepared: PreparedGeometry

    def evaluate(self, current: GeometryValue | EditRejection) -> NeedStoredSpatial | EditRejection:
        if isinstance(current, EditRejection):
            return current
        rejection = check_saved_line(self.baseline, current, self.operation)
        if rejection is not None:
            return rejection
        return NeedStoredSpatial(
            "baseline", self.baseline, current, self.other_changed, self.prepared
        )


@dataclass(frozen=True)
class NeedValidationBaseline:
    eligibility: NeedBaseline
    operation: str | None
    other_changed: bool
    prepared: PreparedGeometry

    def evaluate(self, baseline: GeometryValue | EditRejection) -> NeedCurrent | EditRejection:
        if isinstance(baseline, EditRejection):
            return baseline
        rejection = self.eligibility.evaluate(baseline)
        if rejection is not None:
            return rejection
        return NeedCurrent(baseline, self.operation, self.other_changed, self.prepared)


def begin_save_validation(
    feature_type: str, operation: str | None, other_changed: bool, prepared: PreparedGeometry
) -> NeedValidationBaseline | EditRejection:
    eligibility = begin_baseline(feature_type, operation)
    if isinstance(eligibility, EditRejection):
        return eligibility
    return NeedValidationBaseline(eligibility, operation, other_changed, prepared)
