from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import UserProfile
from src.infra.db.models import UserTable
from src.infra.db.repositories.user_repo import SqlAlchemyUserRepository


@pytest.mark.asyncio
async def test_save_user():
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SqlAlchemyUserRepository(mock_session)

    user = UserProfile(id=uuid4(), email="test@example.com", is_active=True)

    # Act
    await repo.save(user)

    # Assert
    # Verify merge was called
    mock_session.merge.assert_called_once()
    # Check the argument passed to merge is a UserTable
    call_args = mock_session.merge.call_args[0][0]
    assert isinstance(call_args, UserTable)
    assert call_args.id == user.id
    assert call_args.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_by_id_found():
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SqlAlchemyUserRepository(mock_session)
    user_id = uuid4()

    # Simulate DB Row
    mock_row = UserTable(
        id=user_id,
        email="found@example.com",
        is_active=True,
        created_at=datetime.now(UTC),
        experience_years=5,
    )

    # Mock extract scalar result
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_row
    mock_session.execute.return_value = mock_result

    # Act
    result = await repo.get_by_id(user_id)

    # Assert
    assert result is not None
    assert result.id == user_id
    assert result.email == "found@example.com"
    assert result.career.experience_years == 5


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SqlAlchemyUserRepository(mock_session)

    # Mock empty result
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await repo.get_by_id(uuid4())

    # Assert
    assert result is None
