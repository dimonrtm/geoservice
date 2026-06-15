from dataclasses import dataclass
from uuid import UUID

from models.user import UserRole


@dataclass(frozen=True)
class SeedDemoUserSpec:
    id: UUID
    email: str
    password: str
    role: UserRole


SEED_DEMO_USER_SPECS: tuple[SeedDemoUserSpec, ...] = (
    SeedDemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000001"),
        email="alexey.editor@example.local",
        password="alexey-editor-password",
        role=UserRole.EDITOR,
    ),
    SeedDemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000002"),
        email="bolat.editor@example.local",
        password="bolat-editor-password",
        role=UserRole.EDITOR,
    ),
    SeedDemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000003"),
        email="marina.reviewer@example.local",
        password="marina-reviewer-password",
        role=UserRole.REVIEWER,
    ),
)
