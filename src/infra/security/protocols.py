from abc import ABC, abstractmethod


class SecretsBackend(ABC):
    """
    Protocol for secrets backends.
    """

    @abstractmethod
    def get_secret(self, key: str) -> str | None:
        """
        Retrieve a secret by key.
        Returns None if the secret is not found.
        """
        pass
