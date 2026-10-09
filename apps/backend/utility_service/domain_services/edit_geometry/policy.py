from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class UtilityGeometryRoundingMode(str, Enum):
    HALF_AWAY_FROM_ZERO = "ROUND_HALF_AWAY_FROM_ZERO"


@dataclass(frozen=True)
class GeometryPolicy:
    xy_resolution: Decimal
    rounding_mode: str = UtilityGeometryRoundingMode.HALF_AWAY_FROM_ZERO.value
    version: int = 1

    def __post_init__(self) -> None:
        grid = self.xy_resolution
        if (
            not isinstance(
                grid,
                Decimal,
            )
            or not grid.is_finite()
            or not Decimal("0.0000001") <= grid <= Decimal("360")
        ):
            raise ValueError("Шаг координатной сетки должен находиться между 0.0000001 и 360.")
        digits = list(grid.as_tuple().digits)
        exponent = grid.as_tuple().exponent
        while digits and digits[-1] == 0:
            digits.pop()
            exponent += 1
        if exponent < -9:
            raise ValueError("Шаг координатной сетки допускает не более 9 дробных позиций.")
        if self.rounding_mode != UtilityGeometryRoundingMode.HALF_AWAY_FROM_ZERO:
            raise ValueError("Неподдерживаемый режим округления координатной сетки.")
        if type(self.version) is not int or self.version != 1:
            raise ValueError("Неподдерживаемая версия правил обработки геометрии.")
