from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain.entities.memory import MemoryFragment, MemoryKind
from src.domain.entities.user import UserProfile


class TestUserProfile:
    def test_should_create_valid_user(self) -> None:
        user = UserProfile(
            email="test@example.com", full_name="Teo", profession="Coder"
        )
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.profession == "Coder"

    def test_should_reject_tempmail(self) -> None:
        with pytest.raises(ValidationError) as exc:
            UserProfile(email="spammer@tempmail.com")
        assert "Disposable emails are forbidden" in str(exc.value)

    def test_should_remain_immutable(self) -> None:
        user = UserProfile(email="immutable@example.com")
        with pytest.raises(ValidationError):
            user.is_active = False  # type: ignore[misc]

    def test_activate_should_return_new_instance(self) -> None:
        user = UserProfile(email="inactive@example.com", is_active=False)
        activated_user = user.activate()

        assert user.is_active is False
        assert activated_user.is_active is True
        assert activated_user.id == user.id

    def test_update_profession_should_return_new_instance(self) -> None:
        user = UserProfile(email="career@example.com", experience_years=2)
        updated_user = user.update_profession("Senior Dev", 5)

        assert user.profession is None
        assert updated_user.profession == "Senior Dev"
        assert updated_user.experience_years == 5


class TestMemoryFragment:
    def test_should_create_valid_memory(self) -> None:
        mem = MemoryFragment(
            content="Learned Python",
            kind=MemoryKind.SEMANTIC,
            user_id=uuid4(),
            importance=5,
        )
        assert mem.content == "Learned Python"

    def test_should_validate_importance_range(self) -> None:
        with pytest.raises(ValidationError):
            MemoryFragment(
                content="Low", kind=MemoryKind.FACTUAL, user_id=uuid4(), importance=0
            )

        with pytest.raises(ValidationError):
            MemoryFragment(
                content="High", kind=MemoryKind.FACTUAL, user_id=uuid4(), importance=11
            )

    def test_mark_important_should_max_out_importance(self) -> None:
        mem = MemoryFragment(
            content="Important", kind=MemoryKind.EPISODIC, user_id=uuid4(), importance=2
        )
        upgraded = mem.mark_important()
        assert upgraded.importance == 10
        assert mem.importance == 2
