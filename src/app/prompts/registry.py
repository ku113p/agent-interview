import hashlib
from typing import TypedDict


class VariantConfig(TypedDict):
    path: str
    weight: int  # 0-100


class PromptRegistry:
    # Default mapping: logical_key -> filename
    _registry: dict[str, str] = {
        "architect": "architect_v1.j2",
        "critic": "critic_v1.j2",
        "interviewer": "interviewer_v1.j2",
        "summarizer": "summarizer_v1.j2",
    }

    # Variants for A/B testing
    # logical_key -> list of variants
    _variants: dict[str, list[VariantConfig]] = {
        # Example configuration (commented out until needed)
        # "architect": [
        #     {"path": "architect_v1.j2", "weight": 50},
        #     {"path": "architect_v2.j2", "weight": 50},
        # ]
    }

    @classmethod
    def get_template_path(cls, key: str, user_id: str | None = None) -> str:
        """
        Resolves a logical prompt key to a template path.
        If user_id is provided and variants exist, selects a variant deterministically.
        """
        # If the key isn't in our registry, assume it's a direct filename for
        # backward compatibility
        if key not in cls._registry:
            return key

        # Check for A/B testing variants
        if user_id and key in cls._variants:
            variants = cls._variants[key]
            if variants:
                return cls._select_variant(user_id, variants)

        # Fallback to default
        return cls._registry[key]

    @staticmethod
    def _select_variant(user_id: str, variants: list[VariantConfig]) -> str:
        """
        Deterministically selects a variant based on user_id hash.
        """
        # Create a deterministic hash integer from 0-99
        hash_obj = hashlib.md5(user_id.encode("utf-8"))
        hash_int = int(hash_obj.hexdigest(), 16) % 100

        current_threshold = 0
        for variant in variants:
            current_threshold += variant["weight"]
            if hash_int < current_threshold:
                return variant["path"]

        # Fallback to the last variant if something goes wrong (e.g. weights < 100)
        return variants[-1]["path"]
