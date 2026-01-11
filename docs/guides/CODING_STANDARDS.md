# Coding Standards

**Status:** Enforced via CI/CD.
**Policy:** Strict compliance. No "suggestions".

## 1. Python Configuration
All code must comply with the settings defined in `pyproject.toml`.

| Tool | Setting | Value |
| :--- | :--- | :--- |
| **Interpreter** | Python | `3.12+` |
| **Linter** | Ruff | `line-length = 88` |
| **Type Checker** | MyPy | `strict = true` |

## 2. Strict Typing Rules (MyPy)
1.  **No `Any`:** Explicitly define types. If you must use `Any` (e.g., for external libraries), you must comment with `# type: ignore` and a justification.
2.  **Full Signatures:** All functions must return a type.
    ```python
    # BAD
    def process(data): ...

    # GOOD
    def process(data: dict[str, str]) -> None: ...
    ```
3.  **Pydantic Models:** Use Pydantic V2 models for all data structures passing between layers.

## 3. Linting Rules (Ruff)
1.  **Imports:** Sorted automatically (Isort compatible).
2.  **Complexity:** `max-statements = 25`. If a function is longer, refactor it.
3.  **Modern Python:** Use new syntax (e.g., `list[str]` instead of `List[str]`, `X | Y` instead of `Union[X, Y]`).

## 4. Documentation
1.  **Docstrings:** Required for all public modules, classes, and functions. Use Google Style.
2.  **Comments:** Explain *WHY*, not *WHAT*.

## 5. Architecture Enforcement
1.  **Domain Isolation:** `src/domain` must NEVER import from `src/infra`, `src/app`, or `src/entrypoints`.
2.  **Async First:** All I/O bound operations (DB, API) must be `async/await`.
