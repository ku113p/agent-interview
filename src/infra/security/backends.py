import os

import structlog

from src.infra.security.protocols import SecretsBackend

logger = structlog.get_logger()


class EnvSecretsBackend(SecretsBackend):
    """
    Retrieves secrets from environment variables.
    """

    def get_secret(self, key: str) -> str | None:
        # Case-insensitive lookup fallback is handled by Pydantic usually,
        # but here we stick to strict key match or upper case convention
        return os.environ.get(key) or os.environ.get(key.upper())


class FileSecretsBackend(SecretsBackend):
    """
    Retrieves secrets from files (e.g., Docker secrets).
    Expects secrets to be in a directory where filename is the key.
    """

    def __init__(self, secrets_dir: str = "/run/secrets"):
        self.secrets_dir = secrets_dir

    def get_secret(self, key: str) -> str | None:
        # Sanitize key to prevent path traversal
        safe_key = os.path.basename(key)
        secret_path = os.path.join(self.secrets_dir, safe_key)

        if os.path.exists(secret_path):
            try:
                with open(secret_path) as f:
                    return f.read().strip()
            except OSError as e:
                logger.error("file_secret_read_error", key=key, error=str(e))
                return None
        return None


class AWSSecretsManagerBackend(SecretsBackend):
    """
    Retrieves secrets from AWS Secrets Manager.
    Stub implementation.
    """

    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name

    def get_secret(self, key: str) -> str | None:
        # Placeholder for actual AWS implementation
        # Would use boto3.client("secretsmanager").get_secret_value(...)
        logger.warning(
            "aws_secrets_manager_not_implemented",
            key=key,
            msg="Using AWS backend stub. Secret will be None.",
        )
        return None
