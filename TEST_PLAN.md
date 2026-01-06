# Test Plan & Rules

> **Objective:** Maintain high reliability and rapid feedback loop for the Modular Agentic Monolith.
> **Philosophy:** Test-Driven Development (TDD) with a strong preference for unit tests (Speed) and key E2E flows (Confidence).

---

## 1. Testing Strategy (The Pyramid)

We follow the standard Testing Pyramid:

1.  **Unit Tests (70%)**: Fast, isolated, in-memory.
    *   **Scope:** `src/domain`, `src/app/graph` logic, single functions in `src/infra`.
    *   **Mocks:** Heavy usage of Mocks/Fakes for dependencies (e.g., Repo interfaces).
    *   **Location:** `tests/unit/`

2.  **Integration Tests (20%)**: interactions between two layers.
    *   **Scope:** `src/infra` implementations (real DB, Redis), `src/entrypoints` (API routes with faked Service layer).
    *   **Mocks:** Real database (Docker), Mocked 3rd party APIs (OpenAI).
    *   **Location:** `tests/integration/` (To be created)

3.  **E2E Tests (10%)**: Full system flow.
    *   **Scope:** Critical user journeys (e.g., "Interview Candidates", "Refactor Code").
    *   **Mocks:** Minimal. Use real DB, real Redis. VCR/Replay for OpenAI if cost is concern, else real for smoke tests.
    *   **Location:** `tests/e2e_*.py`

---

## 2. Rules for Future Tests

### 2.1 General Rules
*   **Strict Typing:** Tests must pass `mypy` strict mode.
*   **Async First:** Use `@pytest.mark.asyncio` for all async code.
*   **Separation:** Do not mix Unit and Integration tests in the same file if possible.
*   **Fixture-Driven:** Use `conftest.py` for shared setup (DB sessions, Client instantiation).

### 2.2 Naming Conventions
*   **Files:** `test_<feature>.py` or `test_<layer>_<component>.py`.
*   **Functions:** `test_should_<behavior>_when_<condition>` or simple `test_<feature>_<scenario>`.
    *   *Bad:* `test_process`
    *   *Good:* `test_process_should_wait_when_input_is_pending`

### 2.3 Unit Testing (`src/domain` & `src/app`)
*   **No IO:** Unit tests MUST NOT hit the database, network, or disk.
*   **Pure Functions:** Test domain logic by passing data in and asserting return values.
*   **Fakes over Mocks:** Prefer writing a generic `FakeUserRepository(UserRepositoryProtocol)` (in-memory list) over strict `MagicMock` where complex state is needed.

### 2.4 Infra Testing (`src/infra`)
*   **Dockerized Dependencies:** Tests needing DB/Redis must run via `docker-compose` or `testcontainers`. (Currently using project-wide DB).
*   **Cleanup:** Tests must roll back transactions or truncate tables after execution.

---

## 3. Test Implementation Plan (Status)

The following areas have been implemented or are pending:

### 3.1 Domain Layer (Priority: High)
*   [x] **UserProfile Entities:** Verify validation logic (Pydantic constraints).
*   [ ] **Events:** Ensure events are immutable and serializable. *(No event file found)*

### 3.2 App Layer (Priority: High)
*   [x] **Graph Nodes:** Test individual nodes (`Critic`, `Architect`) by mocking the State.
*   [x] **Graph Edges:** Test conditional logic (e.g., `should_continue`).
*   [x] **Prompt Rendering:** Verify Jinja templates render correctly with various inputs.

### 3.3 Infra Layer (Priority: Medium)
*   [x] **Repositories:** Verify `PostgresUserRepository` CRUD operations against a real DB (Integration). *(Existing test: `test_user_repo.py`)*
*   [x] **Vector Store:** Verify Redis vector search/insertion logic.

### 3.4 Entrypoints (Priority: Low - internal use primarily)
*   [x] **API Routes:** Smoke tests for `/message`, `/debug/state` endpoints.

### 3.5 Test Infrastructure (Completed)
*   [x] **Global LLM Mocking:** Auto-detection via `PYTEST_CURRENT_TEST` in `settings.py`
*   [x] **Global Test Fixture:** `conftest.py` with `autouse` fixture for LLM mocking
*   [x] **E2E Tests:** Manual E2E test verified (`e2e_full_cycle.py`)

---

## 4. Running Tests

*   **All Tests:** `uv run pytest`
*   **Unit Only:** `uv run pytest tests/unit`
*   **With Coverage:** `uv run pytest --cov=src`
