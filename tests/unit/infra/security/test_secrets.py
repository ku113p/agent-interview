import os
from unittest.mock import mock_open, patch

from structlog.testing import capture_logs

from src.infra.security.backends import (
    AWSSecretsManagerBackend,
    EnvSecretsBackend,
    FileSecretsBackend,
)
from src.infra.security.manager import SecretsManager
from src.settings import Settings


class TestBackends:
    def test_env_backend(self) -> None:
        with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
            backend = EnvSecretsBackend()
            assert backend.get_secret("TEST_KEY") == "test_value"
            assert backend.get_secret("test_key") == "test_value"  # Fallback to upper

    def test_file_backend(self) -> None:
        with patch("builtins.open", mock_open(read_data="secret_value")):
            with patch("os.path.exists", return_value=True):
                backend = FileSecretsBackend(secrets_dir="/tmp")
                assert backend.get_secret("my_secret") == "secret_value"

    def test_file_backend_not_found(self) -> None:
        with patch("os.path.exists", return_value=False):
            backend = FileSecretsBackend()
            assert backend.get_secret("missing") is None

    def test_aws_backend_stub(self) -> None:
        backend = AWSSecretsManagerBackend()
        with capture_logs() as cap_logs:
            val = backend.get_secret("any")
            assert val is None
            assert len(cap_logs) == 1
            assert cap_logs[0]["event"] == "aws_secrets_manager_not_implemented"


class TestSecretsManager:
    def test_manager_audit_logging_success(self) -> None:
        with patch.dict(os.environ, {"TEST_SECRET": "hush"}):
            manager = SecretsManager(backend_type="env")

            with capture_logs() as cap_logs:
                val = manager.get("TEST_SECRET")

                assert val == "hush"
                # Check for audit log
                audit_logs = [
                    log for log in cap_logs if log["event"] == "secret_accessed"
                ]
                assert len(audit_logs) == 1
                assert audit_logs[0]["key"] == "TEST_SECRET"
                assert audit_logs[0]["backend"] == "env"
                # Ensure value is NOT logged
                assert "hush" not in str(audit_logs[0])

    def test_manager_backend_switching(self) -> None:
        # Test default
        m1 = SecretsManager()
        assert isinstance(m1.backend, EnvSecretsBackend)

        # Test file
        m2 = SecretsManager(backend_type="file")
        assert isinstance(m2.backend, FileSecretsBackend)

        # Test aws
        m3 = SecretsManager(backend_type="aws")
        assert isinstance(m3.backend, AWSSecretsManagerBackend)


class TestSettingsIntegration:
    def test_settings_source_env_override(self) -> None:
        """
        Verify that SecretsSettingsSource works by simulating an environment
        where we want to override a setting using the manager.
        """
        # We'll mock the SecretsManager inside the source to return a value
        with patch("src.infra.security.source.SecretsManager") as MockManager:
            # Setup mock to return a value for OPENAI_API_KEY
            instance = MockManager.return_value
            instance.get.side_effect = (
                lambda k: "sk-mocked-key" if k == "OPENAI_API_KEY" else None
            )

            # Re-initialize settings (this triggers the source loading)
            # We need to ensure required fields are present so validation passes
            with patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "postgresql://user:pass@localhost/db",
                    "REDIS_URL": "redis://localhost:6379/0",
                    "LANGFUSE_PUBLIC_KEY": "pk-lf",
                    "LANGFUSE_SECRET_KEY": "sk-lf",
                    "TELEGRAM_BOT_TOKEN": "123:ABC",
                },
            ):
                # Create a fresh settings instance
                # Note: We can't easily re-instantiate the global 'settings' object
                # safely in parallel tests, so we instantiate the class directly.
                new_settings = Settings()  # type: ignore[call-arg]

                assert new_settings.OPENAI_API_KEY.get_secret_value() == "sk-mocked-key"
                # Verify manager was initialized
                MockManager.assert_called()
