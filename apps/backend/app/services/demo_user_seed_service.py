from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from repositories.user_repository import UserRepository
from services.password_service import hash_password, verify_password


@dataclass(frozen=True)
class DemoUserSpec:
    id: UUID
    email: str
    password: str
    role: UserRole


DEMO_USER_SPECS: tuple[DemoUserSpec, ...] = (
    DemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000001"),
        email="alexey.editor@example.local",
        password="alexey-editor-password",
        role=UserRole.EDITOR,
    ),
    DemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000002"),
        email="bolat.editor@example.local",
        password="bolat-editor-password",
        role=UserRole.EDITOR,
    ),
    DemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000003"),
        email="marina.reviewer@example.local",
        password="marina-reviewer-password",
        role=UserRole.REVIEWER,
    ),
)


class DemoUserSeedService:
    def __init__(self, session: AsyncSession, user_repository: UserRepository):
        self.session = session
        self.user_repository = user_repository

    async def ensure_demo_users(self) -> list[User]:
        seeded_users: list[User] = []

        async with self.session.begin():
            for spec in DEMO_USER_SPECS:
                user = await self.user_repository.get_by_email(spec.email)
                if user is None:
                    user = await self.user_repository.create_user(
                        email=spec.email,
                        role=spec.role,
                        password_hash=hash_password(spec.password),
                        user_id=spec.id,
                    )
                else:
                    role_changed = user.role != spec.role
                    password_changed = not verify_password(spec.password, user.password_hash)
                    active_changed = not user.is_active

                    if role_changed:
                        user.role = spec.role
                    if password_changed:
                        user.password_hash = hash_password(spec.password)
                    if active_changed:
                        user.is_active = True
                    if role_changed or password_changed or active_changed:
                        await self.session.flush()

                seeded_users.append(user)

        return seeded_users


async def run_demo_user_seed() -> list[User]:
    from db.session import SessionFactory

    async with SessionFactory() as session:
        service = DemoUserSeedService(session, UserRepository(session))
        return await service.ensure_demo_users()
