# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2026-01-06] - Exception Handling & Prompt Templates

### Added
- Domain Exception Hierarchy (✅ RA-001)
  - `src/domain/exceptions.py` with DomainError, ResourceNotFound, BusinessRuleViolation
  - `src/entrypoints/api/error_handlers.py` for HTTP error mapping
  - `tests/unit/domain/test_exceptions.py` with full coverage

- Prompt Template System (✅ RA-002)
  - `src/app/prompts/*.j2` Jinja2 templates (critic, interviewer)
  - `src/app/prompts/renderer.py` PromptRenderer service
  - `tests/unit/app/prompts/test_renderer.py`

- Telegram Integration (✅ RA-003)
  - `src/entrypoints/telegram/client.py` Async Telegram Client with retries
  - `src/entrypoints/telegram/webhook.py` Full webhook implementation
  - `tests/unit/entrypoints/telegram/` Unit tests covering client and webhook logic
  - Added `httpx` and `respx` dependencies

### Changed
- Updated `src/infra/llm/client.py` to use LLMError exceptions
- Refactored all graph nodes to use externalized prompt templates
- Updated documentation (TODO.md, docs/architecture/DECISIONS.md)

### Metrics
- Tests: 40/40 passing (100%)
- Code Quality: Mypy strict ✅, Ruff ✅  
- Progress: 2/20 TODO items complete (10%), 2/9 refactorings complete (22%)

### Next Steps
- See [TODO.md](TODO.md) items #3-7 for upcoming high-priority work
- See [docs/planning/README.md](docs/planning/README.md) RA-003 for dependency injection plans

---

