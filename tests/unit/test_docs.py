from pathlib import Path


def test_api_documentation_exists() -> None:
    """
    Verifies that docs/API.md exists and is not empty.
    """
    docs_path = Path(__file__).parent.parent.parent / "docs" / "API.md"
    assert docs_path.exists(), "docs/API.md should exist"
    assert docs_path.stat().st_size > 0, "docs/API.md should not be empty"


def test_architecture_documentation_exists() -> None:
    """
    Verifies that docs/ARCHITECTURE.md exists and is not empty.
    """
    docs_path = Path(__file__).parent.parent.parent / "docs" / "ARCHITECTURE.md"
    assert docs_path.exists(), "docs/ARCHITECTURE.md should exist"
    assert docs_path.stat().st_size > 0, "docs/ARCHITECTURE.md should not be empty"


def test_openapi_schema_generator_exists() -> None:
    """
    Verifies that scripts/generate_schema.py exists.
    """
    script_path = Path(__file__).parent.parent.parent / "scripts" / "generate_schema.py"
    assert script_path.exists(), "scripts/generate_schema.py should exist"
