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

### Changed
- Updated `src/infra/llm/client.py` to use LLMError exceptions
- Refactored all graph nodes to use externalized prompt templates
- Updated documentation (TODO.md, REFACTORING_PLAN.md, ARCHITECTURE_DECISIONS.md)

### Metrics
- Tests: 40/40 passing (100%)
- Code Quality: Mypy strict ✅, Ruff ✅  
- Progress: 2/20 TODO items complete (10%), 2/9 refactorings complete (22%)

### Next Steps
- See [TODO.md](TODO.md) items #3-7 for upcoming high-priority work
- See [docs/planning/REFACTORING.md](docs/planning/REFACTORING.md) RA-003 for dependency injection plans

---

*For detailed session notes, see [docs/archive/SESSION_2026-01-06.md](docs/archive/SESSION_2026-01-06.md)*
