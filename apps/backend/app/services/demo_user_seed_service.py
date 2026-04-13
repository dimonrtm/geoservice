from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from repositories.user_repository import UserRepository
from services.password_service import hash_password, verify_password


@dataclass(frozen=True)
class DemoUserSpec:
    email: str
    password: str
    role: UserRole


DEMO_USER_SPECS: tuple[DemoUserSpec, ...] = (
    DemoUserSpec(
        email="editor@example.com",
        password="editor-password",
        role=UserRole.EDITOR,
    ),
    DemoUserSpec(
        email="viewer@example.com",
        password="viewer-password",
        role=UserRole.VIEWER,
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
                    )
                else:
                    role_changed = user.role != spec.role
                    password_changed = not verify_password(spec.password, user.password_hash)

                    if role_changed:
                        user.role = spec.role
                    if password_changed:
                        user.password_hash = hash_password(spec.password)
                    if role_changed or password_changed:
                        await self.session.flush()

                seeded_users.append(user)

        return seeded_users


async def run_demo_user_seed() -> list[User]:
    from db.session import SessionFactory

    async with SessionFactory() as session:
        service = DemoUserSeedService(session, UserRepository(session))
        return await service.ensure_demo_users()
