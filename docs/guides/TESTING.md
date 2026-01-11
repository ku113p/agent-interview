# Testing Strategy

**Status:** Active.
**Framework:** `pytest` + `pytest-asyncio`.

## 1. Test Pyramid
We follow a strict testing pyramid to ensure speed and reliability.

### Level 1: Unit Tests (`tests/unit/`)
*   **Scope:** Isolate Domain entities and Application Services.
*   **Dependencies:** All external dependencies (DB, LLM, Memory) must be **MOCKED**.
*   **Speed:** < 10ms per test.
*   **Command:** `uv run pytest tests/unit`

### Level 2: Integration Tests (`tests/integration/`)
*   **Scope:** Verify interactions between Adapters and external infrastructure (Docker).
*   **Dependencies:** Real Postgres, Real Redis (via `docker-compose.yml`).
*   **Speed:** Slow. Run in CI or pre-commit.
*   **Command:** `uv run pytest tests/integration`

## 2. Writing Tests

### Naming Convention
*   Files: `test_<module>.py`
*   Functions: `test_<function>_<scenario>_<expected_result>`

### Async Support
All async tests must use the `pytest.mark.asyncio` marker (handled automatically by `asyncio_mode = "auto"` in `pyproject.toml`).

```python
import pytest

@pytest.mark.asyncio
async def test_create_user_success():
    # Arrange
    ...
    # Act
    result = await service.create(...)
    # Assert
    assert result.id is not None
```

## 3. Mocking Strategy
Use `unittest.mock` or `respx` (for HTTP).

```python
from unittest.mock import AsyncMock

async def test_service_calls_repo():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = UserProfile(...)
    
    service = UserService(repo=mock_repo)
    await service.get_user("123")
    
    mock_repo.get_by_id.assert_called_once()
```
