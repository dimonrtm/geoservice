from sqlalchemy.ext.asyncio import AsyncSession

from core.passwords import hash_password, verify_password
from models.user import User
from seeds.repositories.seed_user_repository import SeedUserRepository
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS


class SeedDemoUserService:
    def __init__(
        self,
        session: AsyncSession,
        repository: SeedUserRepository,
    ):
        self.session = session
        self.repository = repository

    async def ensure_demo_users(self) -> list[User]:
        seeded_users: list[User] = []

        async with self.session.begin():
            for spec in SEED_DEMO_USER_SPECS:
                user = await self.repository.get_by_email(spec.email)
                if user is None:
                    user = await self.repository.create_user(
                        email=spec.email,
                        role=spec.role,
                        password_hash=hash_password(spec.password),
                        user_id=spec.id,
                    )
                else:
                    role_changed = user.role != spec.role
                    password_changed = not verify_password(
                        spec.password,
                        user.password_hash,
                    )
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


async def run_seed_demo_users() -> list[User]:
    from db.session import SessionFactory

    async with SessionFactory() as session:
        return await SeedDemoUserService(
            session,
            SeedUserRepository(session),
        ).ensure_demo_users()
