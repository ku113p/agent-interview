# Agent Playbook

Short guidance for AI agents working in `agent-interview`.

## Mission
- Drive the Deep Profiling & Biography Agent: collect biographies through LangGraph workflows.
- Roles:
  - **Architect** plans Spheres (childhood, career, etc.) and builds interview sequences.
  - **Interviewer** executes the plan, collects answers, and emits facts.
  - **Critic** validates every answer for completeness before the session advances.
- Keep the focus on accuracy, observability, and graceful retries.

## Workflow
1. **Summarizer** compresses conversation history to maintain context window efficiency.
2. **Architect** composes a plan via LangGraph, then hands the plan to the Critic.
3. **Critic** reviews the plan for safety and quality.
4. **Interviewer** drives the dialogue based on the approved plan, stores memory in Mem0/Redis, and records state updates.
5. Repeat until the profile meets completeness criteria; observe via LangFuse spans and logs.

## Stack
- **Language**: Python 3.12 with `uv` package management.
- **Framework**: FastAPI + LangGraph for graph-based workflows.
- **Storage**: Postgres for relational data, Redis/Mem0 for memory, LangFuse for tracing.
- **Agents**: Architect / Interviewer / Critic nodes live under `src/app/graph/nodes/*`.

## Key docs
- `docs/architecture/CONTEXT.md` — repo map, critical invariants, and essentials.
- `docs/architecture/PATTERNS.md` — domain/ports/services/prompt/testing pattern reminders.
- `docs/architecture/DECISIONS.md` — compact ADRs (LangGraph triad, hexagonal boundaries, observability, tooling).
- `docs/guides/CODING_STANDARDS.md` — tooling rules (uv, Ruff, mypy) and typing expectations.
- `docs/guides/TESTING.md` — test pyramid, directories, and commands.

## Editing rules
- Prefer short, imperative bullets; skip marketing or persona roleplay.
- Keep references accurate: no `docs/archive/**` or deleted planning files.
- Inline facts with code status, not speculation.
- All planning information belongs here; avoid adding new planning documents elsewhere.
