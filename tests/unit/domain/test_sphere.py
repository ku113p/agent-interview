from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain.entities.sphere import Sphere, SphereStatus


class TestSphere:
    def test_should_create_valid_sphere(self) -> None:
        user_id = uuid4()
        sphere = Sphere(
            user_id=user_id,
            name="Career",
            description="Professional journey",
        )
        assert sphere.user_id == user_id
        assert sphere.name == "Career"
        assert sphere.description == "Professional journey"
        assert sphere.status == SphereStatus.NOT_STARTED

    def test_should_reject_empty_name(self) -> None:
        with pytest.raises(ValueError):
            Sphere(user_id=uuid4(), name="")

    def test_should_remain_immutable(self) -> None:
        sphere = Sphere(user_id=uuid4(), name="Test")
        with pytest.raises(ValidationError):
            sphere.name = "Changed"  # type: ignore[misc]

    def test_start_session_should_transition_to_in_progress(self) -> None:
        sphere = Sphere(user_id=uuid4(), name="Test")
        started = sphere.start_session()
        assert started.status == SphereStatus.IN_PROGRESS
        assert started != sphere  # Different instance

    def test_start_session_should_reject_completed_sphere(self) -> None:
        sphere = Sphere(user_id=uuid4(), name="Test", status=SphereStatus.COMPLETED)
        with pytest.raises(
            ValueError, match="Cannot start session on completed sphere"
        ):
            sphere.start_session()

    def test_complete_should_transition_to_completed(self) -> None:
        sphere = Sphere(user_id=uuid4(), name="Test", status=SphereStatus.IN_PROGRESS)
        completed = sphere.complete()
        assert completed.status == SphereStatus.COMPLETED
        assert completed != sphere  # Different instance
