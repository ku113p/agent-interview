# Architecture Decision Records (ADR)

Condense each decision to what matters for running AI agents today: why, what changed, and how to keep stability.

---

## 1. Core Architecture & Patterns

### ADR-001: The "Base-Interviewer-Architect" Triad
* **Status:** Accepted
* [cite_start]**Context:** Monolithic LLM approaches fail to maintain long-term context and cannot simultaneously handle empathetic conversation and strategic data profiling without cognitive overload or hallucinations[cite: 81, 91].
* [cite_start]**Decision:** Implement the **Planner-Executor-Observer** pattern[cite: 86, 93].
    1.  [cite_start]**The Architect (Planner):** An asynchronous "Slow Loop" component (e.g., GPT-4o) that analyzes memory gaps and generates strategic instructions[cite: 118, 162].
    2.  [cite_start]**The Interviewer (Executor):** A synchronous "Fast Loop" component (e.g., GPT-4o-mini) that handles real-time user interaction, tone adaptation, and active listening[cite: 140, 159].
    3.  [cite_start]**The Base (Observer):** A polyglot memory system that acts as the source of truth[cite: 84, 97].
* [cite_start]**Consequences:** separation of concerns allows for deterministic behavior in data collection while maintaining conversational fluidity[cite: 92].

### ADR-002: Hexagonal Architecture (Ports & Adapters)
* **Status:** Accepted
* [cite_start]**Context:** The business logic must remain decoupled from specific infrastructure details like OpenAI APIs, Telegram webhooks, or specific database drivers to ensure maintainability[cite: 27, 39].
* **Decision:** Adhere to strictly decoupled architecture:
    * **Domain:** Pure Pydantic models and logic. [cite_start]No imports from `sqlalchemy` or `langchain` allowed[cite: 42].
    * [cite_start]**Ports:** Interfaces defining contracts (e.g., `UserRepositoryProtocol`, `LLMProviderProtocol`)[cite: 44, 45].
    * [cite_start]**Adapters:** Infrastructure implementations (e.g., `SqlAlchemyUserRepository`)[cite: 46, 50].
* [cite_start]**Consequences:** Enables easy swapping of LLM providers (e.g., OpenAI to Local Llama) and simplifies unit testing via mocking[cite: 45, 58].

### ADR-003: State Management via LangGraph
* **Status:** Accepted
* [cite_start]**Context:** The agent workflow requires cycles (loops), conditional edges (critique/retry), and persistent state across long-running conversations[cite: 60, 64]. Linear chains are insufficient.
* [cite_start]**Decision:** Use **LangGraph** (`StateGraph`) for orchestration[cite: 22].
* [cite_start]**Consequences:** Provides native support for cyclic graphs, state persistence via checkpointers (AsyncPostgresSaver), and complex multi-agent flows[cite: 65, 179].

---

## 2. Data Strategy & Memory

### ADR-004: Polyglot Persistence (Hybrid Memory)
* **Status:** Accepted
* [cite_start]**Context:** Different types of human memory (semantic vs. episodic vs. factual) require different storage engines for efficient retrieval[cite: 97].
* **Decision:**
    1.  [cite_start]**PostgreSQL (Relational):** For core profile attributes, strict schemas, and critical business data[cite: 108, 112].
    2.  [cite_start]**Redis (Vector):** For semantic search, associative memory, and caching embeddings[cite: 51, 98].
    3.  [cite_start]**JSON-LD:** Use Linked Data standards for ontology to ensure semantic context for all data fields[cite: 115].
* [cite_start]**Consequences:** Requires implementation of "Dual-Write" logic to ensure facts are saved to both Postgres (reliability) and Redis (search)[cite: 52].

### ADR-005: Strict Data Validation
* **Status:** Accepted
* **Context:** LLMs are prone to generating unstructured or malformed data, leading to downstream system errors.
* **Decision:** Use **Pydantic V2** for all data schemas. [cite_start]Every LLM call must utilize structured outputs defined by Pydantic models[cite: 13, 55].
* [cite_start]**Consequences:** Prevents "type hallucinations" (e.g., string in an integer field) and ensures code is compatible with `mypy --strict`[cite: 11, 115].

---

## 3. Tooling & Development Standards

### ADR-006: Package Management via `uv`
* **Status:** Accepted
* **Context:** Traditional Python package managers (pip, poetry) are slower and can be complex to manage in CI/CD.
* **Decision:** ALWAYS use `uv` for package operations (`uv add`, `uv sync`, `uv run`). [cite_start]Usage of `pip` or `conda` is forbidden[cite: 3, 4].
* [cite_start]**Consequences:** Significantly faster environment setup and dependency resolution[cite: 5].

### ADR-007: Static Analysis & Strict Typing
* **Status:** Accepted
* **Context:** Python's dynamic nature can lead to runtime errors that are hard to debug in complex agentic systems.
* **Decision:**
    * **Mypy:** Must pass `mypy --strict`. [cite_start]No implicit `Any` allowed[cite: 11, 12].
    * **Ruff:** Used for both linting and formatting. [cite_start]Line limits set to 88/100 chars[cite: 7, 8].
* [cite_start]**Consequences:** Forces explicit type definitions and adherence to protocols, reducing bugs before runtime[cite: 12].

### ADR-008: Async-First Database Interaction
* **Status:** Accepted
* **Context:** The system is IO-bound (waiting on LLMs and DBs). Blocking calls will degrade performance.
* **Decision:** Use **SQLAlchemy 2.0+** with `AsyncSession`. [cite_start]Legacy `session.query()` is prohibited[cite: 23].
* **Consequences:** All repository interactions must be `await`-able.

---

## 4. Observability & Security

### ADR-009: Deep Tracing with LangFuse
* **Status:** Accepted
* **Context:** Debugging "Chain-of-Thought" logic is impossible with standard logging alone.
* [cite_start]**Decision:** Integrate **LangFuse** (self-hosted via Docker) for full LLM tracing, token counting, and evaluation[cite: 37, 66].
* [cite_start]**Consequences:** Requires `@observe` decorators on graph entry points[cite: 66].

### ADR-010: Prompt Injection Defense
* **Status:** Accepted
* **Context:** Malicious users may attempt to override agent instructions.
* **Decision:**
    1.  [cite_start]**Context Separation:** Isolate user input using delimiters (e.g., XML tags)[cite: 187].
    2.  [cite_start]**Dual LLM Pattern:** Use a lightweight "censor" model to check inputs before they reach the main Interviewer agent[cite: 188].
* **Consequences:** Adds a small latency overhead but significantly increases security.

### ADR-011: Prompt Injection Defense
* **Status:** Accepted
* [cite_start]**Context:** Malicious users may attempt to override agent instructions (e.g., "Ignore all previous instructions")[cite: 186].
* **Decision:**
    1.  [cite_start]**Context Separation:** Isolate user input using delimiters (e.g., XML tags like `<user_input>`)[cite: 187].
    2.  [cite_start]**Dual LLM Pattern:** Use a lightweight "censor" model to check inputs for attacks before they reach the main Interviewer agent[cite: 188].
* **Consequences:** Adds a small latency overhead but significantly increases security against social engineering attacks.

---

## 5. Error Handling \u0026 Maintainability

### ADR-012: Domain Exception Hierarchy
* **Status:** \u2705 **Implemented** (2026-01-06)
* **Context:** Generic exceptions (`Exception`, `ValueError`) make it difficult to distinguish business rule violations from infrastructure failures and map errors to appropriate HTTP status codes.
* **Decision:** 
    1. Create a typed domain exception hierarchy in `src/domain/exceptions.py`
    2. All domain layer code must raise specific exceptions (`DomainError`, `ResourceNotFound`, `BusinessRuleViolation`)
    3. FastAPI exception handlers map domain exceptions to HTTP statuses (404, 400, 500)
    4. LLM errors use specialized `LLMError`, `LLMTimeoutError`, `LLMResponseError`
* **Consequences:** 
    - Improved error diagnostics and debugging
    - Automatic, consistent API error responses
    - Clear separation between domain logic and HTTP concerns
    - Enables proper error telemetry and alerting
* **Implementation:** See `src/domain/exceptions.py`, `src/entrypoints/api/error_handlers.py`

### ADR-013: Externalized Prompt Templates
* **Status:** \u2705 **Implemented** (2026-01-06)
* **Context:** Hardcoded prompts in Python code make it impossible to iterate on prompt engineering without code changes, preventing A/B testing and versioning.
* **Decision:**
    1. All system prompts must be defined in Jinja2 templates (`src/app/prompts/*.j2`)
    2. Use `PromptRenderer` service to render templates with context
    3. Prompts are versioned by filename (e.g., `architect_v1.j2`, `critic_v2.j2`)
    4. Zero hardcoded prompt strings in graph nodes
* **Consequences:**
    - Enables rapid prompt iteration without code deployment
    - A/B testing ready (can swap templates via config)
    - Prompts are reviewable as separate files in version control
    - Non-engineers can modify prompts safely
* **Implementation:** See `src/app/prompts/renderer.py`, `src/app/prompts/*.j2`

---

## 6. Implementation Progress

**Completed ADRs**:
- \u2705 ADR-001 through ADR-011 (original design)
- \u2705 ADR-012: Domain Exception Hierarchy
- \u2705 ADR-013: Externalized Prompt Templates

**In Progress**: None

**Planned**: Memory integration, dependency injection refactoring
