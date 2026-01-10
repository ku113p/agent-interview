class DomainError(Exception):
    """Base class for all domain exceptions."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ResourceNotFound(DomainError):
    """Raised when a requested resource does not exist."""

    pass


class BusinessRuleViolation(DomainError):
    """Raised when a business rule is violated."""

    pass


class UserNotFoundError(ResourceNotFound):
    """Raised when a user is not found."""

    pass


class MemoryNotFoundError(ResourceNotFound):
    """Raised when a memory fragment is not found."""

    pass


class LLMError(DomainError):
    """Base class for LLM related errors."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when the LLM call times out."""

    pass


class LLMResponseError(LLMError):
    """Raised when the LLM returns an invalid or unexpected response."""

    pass


class LLMMessageValidationError(LLMError):
    """Raised when message input validation fails."""

    pass
