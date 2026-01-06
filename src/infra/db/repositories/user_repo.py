from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import UserProfile
from src.domain.ports.user_repository import UserRepositoryProtocol
from src.infra.db.models import UserTable


class SqlAlchemyUserRepository(UserRepositoryProtocol):
    """Implementation of the Port using Postgres."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserProfile | None:
        query = select(UserTable).where(UserTable.id == user_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        return self._to_domain(row)

    async def get_by_email(self, email: str) -> UserProfile | None:
        query = select(UserTable).where(UserTable.email == email)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None
        return self._to_domain(row)

    async def save(self, user: UserProfile) -> None:
        record = UserTable(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            full_name=user.full_name,
            profession=user.profession,
            experience_years=user.experience_years,
        )

        await self._session.merge(record)

    def _to_domain(self, row: UserTable) -> UserProfile:
        return UserProfile(
            id=row.id,
            email=row.email,
            is_active=row.is_active,
            created_at=row.created_at,
            full_name=row.full_name,
            profession=row.profession,
            experience_years=row.experience_years,
        )
