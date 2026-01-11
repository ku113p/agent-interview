from typing import Any

import structlog

from src.infra.security.backends import (
    AWSSecretsManagerBackend,
    EnvSecretsBackend,
    FileSecretsBackend,
)
from src.infra.security.protocols import SecretsBackend

logger = structlog.get_logger()


class SecretsManager:
    """
    Manager to handle secret retrieval from configured backend.
    """

    def __init__(self, backend_type: str = "env", **kwargs: Any):
        self.backend_type = backend_type
        self.backend: SecretsBackend

        if backend_type == "file":
            self.backend = FileSecretsBackend(**kwargs)
        elif backend_type == "aws":
            self.backend = AWSSecretsManagerBackend(**kwargs)
        else:
            self.backend = EnvSecretsBackend()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a secret value. Logs the access (audit).
        """
        val = self.backend.get_secret(key)

        # Audit logging: Log that a secret was accessed (do NOT log the value)
        if val is not None:
            logger.info("secret_accessed", key=key, backend=self.backend_type)
            return val

        return default
