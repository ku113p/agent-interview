# Agent Playbook

**Status:** Active | **Role:** Single Source of Truth

## Mission
Develop an **Autonomous Dialogue System** ("Deep Profiling & Biography Agent") that collects user biographies through natural conversation. The system must utilize a multi-agent workflow to plan, execute, and validate interviews, ensuring data accuracy and long-term memory retention.

## Workflow (The "Brain")
1.  **Summarizer:** Compresses conversation history to maintain context efficiency.
2.  **Architect:** Analyzes memory (`Mem0`), plans "Spheres" (Childhood, Career), and builds interview graphs.
3.  **Critic:** Validates the Architect's plan for safety, logic, and completeness *before* execution.
4.  **Interviewer:** Executes the approved plan, conducting the dialogue and emitting facts to memory.

## Tech Stack (Verified)
- **Core:** Python 3.12+ (Strict Mode)
- **Package Manager:** `uv`
- **Orchestration:** LangGraph (Stateful Workflows)
- **API:** FastAPI + Uvicorn
- **Memory/Storage:**
    - `mem0ai`: Vector Memory
    - `redis`: Caching
    - `postgres`: Application Data & Checkpoints
- **Observability:** LangFuse (Tracing)
- **Testing:** `pytest` (Async), `ruff` (Linting), `mypy` (Strict Typing)

## Documentation Index
- **Architecture:**
    - [`docs/architecture/CONTEXT.md`](../architecture/CONTEXT.md): Repository map & System Invariants.
    - [`docs/architecture/PATTERNS.md`](../architecture/PATTERNS.md): Design patterns (Nodes, Prompts).
    - [`docs/architecture/DECISIONS.md`](../architecture/DECISIONS.md): Architectural Decision Records (ADRs).
- **Guides:**
    - [`docs/guides/CODING_STANDARDS.md`](../guides/CODING_STANDARDS.md): Linting, Typing, and Style.
    - [`docs/guides/TESTING.md`](../guides/TESTING.md): Testing strategy and commands.

## Directory Map
- `src/app/graph/nodes/`: Agent implementations (Architect, Critic, etc.).
- `src/domain/`: Core entities and Pydantic models.
- `docs/planning/`: **YOU ARE HERE** (The Playbook).
- `docs/architecture/`: Detailed system design and ADRs.

## Editing Rules
- **No Fluff:** Keep documentation technical and directive.
- **No Fragmentation:** Do not create `docs/archive` or side-planning files. Update this Playbook instead.
- **Invariants:**
    - The Critic never edits memory directly.
    - All external I/O goes through `entrypoints`.
