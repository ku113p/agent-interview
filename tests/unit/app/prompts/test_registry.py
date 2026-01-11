from src.app.prompts.registry import PromptRegistry


def test_registry_get_default():
    # Assuming "architect" defaults to "architect_v1.j2"
    template = PromptRegistry.get_template_path("architect")
    assert template == "architect_v1.j2"


def test_registry_unknown_returns_key():
    # If a key is not in registry, it should return the key itself
    # (backward compatibility)
    template = PromptRegistry.get_template_path("unknown_template.j2")
    assert template == "unknown_template.j2"


def test_registry_ab_testing_selection():
    # Mock the registry for testing
    original_registry = PromptRegistry._registry
    original_variants = PromptRegistry._variants

    try:
        PromptRegistry._registry = {"test_prompt": "default.j2"}
        PromptRegistry._variants = {
            "test_prompt": [
                {"path": "variant_a.j2", "weight": 50},
                {"path": "variant_b.j2", "weight": 50},
            ]
        }

        # Test deterministic selection
        # user_1 should always get the same variant
        v1 = PromptRegistry.get_template_path("test_prompt", user_id="user_1")
        v2 = PromptRegistry.get_template_path("test_prompt", user_id="user_1")
        assert v1 == v2

        # Different users might get different variants (probabilistic)
        # We can't guarantee they are different without checking the hash logic,
        # but we can check they are valid.
        assert v1 in ["variant_a.j2", "variant_b.j2"]

    finally:
        PromptRegistry._registry = original_registry
        PromptRegistry._variants = original_variants
