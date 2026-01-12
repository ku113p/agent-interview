from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import UserProfile
from src.domain.ports.user_repository import UserRepositoryProtocol


class SqlAlchemyUserRepository(UserRepositoryProtocol):
    """
    SQLAlchemy implementation of UserRepository.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserProfile | None:
        from src.infra.db.models import UserTable

        query = select(UserTable).where(UserTable.id == user_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        return self._to_domain(row)

    async def get_by_email(self, email: str) -> UserProfile | None:
        from src.infra.db.models import UserTable

        query = select(UserTable).where(UserTable.email == email)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None
        return self._to_domain(row)

    async def list_all(self, limit: int, offset: int) -> list[UserProfile]:
        from src.infra.db.models import UserTable

        query = select(UserTable).limit(limit).offset(offset)
        result = await self._session.execute(query)
        rows = result.scalars().all()

        return [self._to_domain(row) for row in rows]

    async def save(self, user: UserProfile) -> None:
        from src.infra.db.models import UserTable

        profession = user.career.profession if user.career else None
        experience_years = user.career.experience_years if user.career else 0

        record = UserTable(
            id=user.id,
            email=user.email.value,
            is_active=user.is_active,
            created_at=user.created_at,
            full_name=user.full_name,
            profession=profession,
            experience_years=experience_years,
        )

        await self._session.merge(record)

    def _to_domain(self, row: object) -> UserProfile:
        from typing import Any
        from src.domain.entities.user import Career, EmailAddress

        r: Any = row

        career = None
        if r.profession or r.experience_years:
            career = Career(
                profession=r.profession or "", experience_years=r.experience_years or 0
            )

        return UserProfile(
            id=r.id,
            email=EmailAddress(value=r.email),
            is_active=r.is_active,
            created_at=r.created_at,
            full_name=r.full_name,
            career=career,
        )
