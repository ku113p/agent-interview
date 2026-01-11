import os
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import PydanticBaseSettingsSource

from src.infra.security.manager import SecretsManager


class SecretsSettingsSource(PydanticBaseSettingsSource):
    """
    Custom Pydantic settings source that retrieves values from the configured
    SecretsManager backend.
    """

    def __init__(self, settings_cls: type[Any]):
        super().__init__(settings_cls)
        # Determine backend from env var, default to "env"
        backend_type = os.environ.get("SECRETS_BACKEND", "env").lower()
        self.secrets_manager = SecretsManager(backend_type=backend_type)

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        """
        Get the value for a field from the secrets manager.
        """
        # Try exact match first
        val = self.secrets_manager.get(field_name)
        if val is not None:
            return val, field_name, False

        # Try upper case (common for env/secrets)
        val = self.secrets_manager.get(field_name.upper())
        if val is not None:
            return val, field_name, False

        # Return None if not found, letting Pydantic try other sources
        return None, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        # Standard preparation
        return value

    def __call__(self) -> dict[str, Any]:
        # Iterate over all fields in the settings class and try to fetch them
        d: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            value, _, _ = self.get_field_value(field, field_name)
            if value is not None:
                d[field_name] = value
        return d
