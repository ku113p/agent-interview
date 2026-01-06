from src.domain.exceptions import (
    BusinessRuleViolation,
    DomainError,
    MemoryNotFoundError,
    ResourceNotFound,
    UserNotFoundError,
)


def test_exception_hierarchy():
    assert issubclass(ResourceNotFound, DomainError)
    assert issubclass(BusinessRuleViolation, DomainError)
    assert issubclass(UserNotFoundError, ResourceNotFound)
    assert issubclass(MemoryNotFoundError, ResourceNotFound)

def test_exception_messages():
    err = UserNotFoundError("User 123 not found")
    assert str(err) == "User 123 not found"
    assert err.message == "User 123 not found"
