from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.entities.sphere import Sphere, SphereStatus
from src.domain.entities.user import UserProfile
from src.infra.db.repositories.sphere_repo import SqlAlchemySphereRepository
from src.infra.db.repositories.user_repo import SqlAlchemyUserRepository


@pytest.mark.asyncio
async def test_user_repository_integration(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user_id = uuid4()
    email = f"test_{user_id}@example.com"

    # Create User
    user = UserProfile(
        id=user_id,
        email=email,
        is_active=True,
        created_at=datetime.now(UTC),
        full_name="Integration Test User",
        profession="Engineer",
        experience_years=5,
    )

    await repo.save(user)
    await db_session.flush()  # Ensure it hits the DB

    # Retrieve User
    retrieved = await repo.get_by_id(user_id)
    assert retrieved is not None
    assert retrieved.id == user_id
    assert retrieved.email == email
    assert retrieved.profession == "Engineer"

    # Retrieve by Email
    by_email = await repo.get_by_email(email)
    assert by_email is not None
    assert by_email.id == user_id


@pytest.mark.asyncio
async def test_sphere_repository_integration(db_session):
    # Setup User first (Foreign Key constraint)
    user_repo = SqlAlchemyUserRepository(db_session)
    user_id = uuid4()
    user = UserProfile(
        id=user_id, email=f"sphere_owner_{user_id}@example.com", is_active=True
    )
    await user_repo.save(user)
    await db_session.flush()

    # Setup Sphere Repo
    sphere_repo = SqlAlchemySphereRepository(db_session)
    sphere_id = uuid4()

    sphere = Sphere(
        id=sphere_id,
        user_id=user_id,
        name="Career Growth",
        description="Planning my next promotion",
        status=SphereStatus.IN_PROGRESS,
        created_at=datetime.now(UTC),
    )

    # Save
    await sphere_repo.save(sphere)
    await db_session.flush()

    # Retrieve
    retrieved = await sphere_repo.get_by_id(sphere_id)
    assert retrieved is not None
    assert retrieved.name == "Career Growth"
    assert retrieved.status == SphereStatus.IN_PROGRESS

    # List by User
    spheres = await sphere_repo.get_by_user_id(user_id)
    assert len(spheres) == 1
    assert spheres[0].id == sphere_id

    # Delete
    await sphere_repo.delete(sphere_id)
    await db_session.flush()

    deleted = await sphere_repo.get_by_id(sphere_id)
    assert deleted is None
