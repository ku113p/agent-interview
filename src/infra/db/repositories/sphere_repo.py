from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.sphere import Sphere
from src.domain.ports.sphere_repository import SphereRepositoryProtocol
from src.infra.db.models import SphereTable


class SqlAlchemySphereRepository(SphereRepositoryProtocol):
    """Implementation of SphereRepository using Postgres."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, sphere_id: UUID) -> Sphere | None:
        query = select(SphereTable).where(SphereTable.id == sphere_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        return self._to_domain(row)

    async def get_by_user_id(self, user_id: UUID) -> list[Sphere]:
        query = select(SphereTable).where(SphereTable.user_id == user_id)
        result = await self._session.execute(query)
        rows = result.scalars().all()

        return [self._to_domain(row) for row in rows]

    async def save(self, sphere: Sphere) -> None:
        record = SphereTable(
            id=sphere.id,
            user_id=sphere.user_id,
            name=sphere.name,
            description=sphere.description,
            status=sphere.status.value,
            created_at=sphere.created_at,
        )

        await self._session.merge(record)

    async def delete(self, sphere_id: UUID) -> None:
        # Note: In a real app, this might be a soft delete
        # For now, hard delete
        query = select(SphereTable).where(SphereTable.id == sphere_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if row:
            await self._session.delete(row)

    def _to_domain(self, row: SphereTable) -> Sphere:
        from src.domain.entities.sphere import SphereStatus

        return Sphere(
            id=row.id,
            user_id=row.user_id,
            name=row.name,
            description=row.description,
            status=SphereStatus(row.status),
            created_at=row.created_at,
        )
