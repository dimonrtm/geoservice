from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole


class SeedUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().one_or_none()

    async def create_user(
        self,
        *,
        email: str,
        role: UserRole,
        password_hash: str,
        user_id: UUID,
    ) -> User:
        result = await self.session.execute(
            insert(User)
            .values(
                id=user_id,
                email=email,
                role=role,
                password_hash=password_hash,
            )
            .returning(User)
        )
        return result.scalar_one()
