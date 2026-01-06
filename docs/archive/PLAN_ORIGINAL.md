# 🚀 Master Implementation Plan: Modular Agentic Monolith

**Classification:** Enterprise Grade / Self-Hosted
**Architecture:** Hexagonal (Ports & Adapters)
**Tech Stack:** Python 3.14+, `uv`, LangGraph, FastAPI, PostgreSQL (Async), Redis, LangFuse (Docker).

---

## 🏗 Phase 0: The "Ironclad" Foundation
**Goal:** Setup a dev environment that forbids bad code by design.

- [x] **0.1. Workspace & Tooling (Strict)**
    - [x] `uv init` & `uv python install 3.14`.
    - [x] **Dependency Grouping:** Separate `core` (langgraph, pydantic), `infra` (sqlalchemy, redis), `dev` (mypy, ruff, pytest).
    - [x] **Pre-commit Hooks:**
        -   `ruff check --fix` (Linting).
        -   `ruff format` (Style).
        -   `mypy --strict` (Type Safety).
        -   `uv run pytest tests/unit` (Instant feedback).
    - [x] **Environment Config:** Use `pydantic-settings` with strict validation. Fail fast if `OPENAI_API_KEY` or `DATABASE_URL` is missing.

- [x] **0.2. Self-Hosted Infrastructure (Docker)**
    - [x] `docker-compose.yml` services:
        -   **`postgres`**: Ver 16-alpine. Mount volumes for persistence.
        -   **`redis`**: Redis Stack (w/ Search module).
        -   **`langfuse`**: For LLM Tracing & Eval (Port 3000).
    - [x] **Healthchecks:** Add `healthcheck` blocks to containers. The app must wait for DBs to be healthy before starting.

---

## 🧩 Phase 1: Domain-Driven Design (The Core)
**Goal:** Define business logic that is strictly decoupled from the database or API.

- [x] **1.1. Pure Domain Entities (`src/domain/entities`)**
    - [x] `UserProfile`: The aggregate root.
    - [x] `MemoryFragment`: A value object for a piece of information.
    - [x] **Rule:** These are pure Pydantic models. NO imports from `sqlalchemy` or `langchain` allowed here.

- [x] **1.2. Interfaces/Ports (`src/domain/ports`)**
    - [x] `UserRepositoryProtocol`: Interface for saving users.
    - [x] `MemoryServiceProtocol`: Interface for semantic search.
    - [x] `LLMProviderProtocol`: Abstract interface for generation (allows swapping OpenAI <-> Anthropic <-> Local Llama).

---

## 💾 Phase 2: Infrastructure Adapters
**Goal:** Implement the "dirty" details (SQL, Vectors) keeping the Core clean.

- [x] **2.1. Persistence Adapter (`src/infra/db`)**
    - [x] **SQLAlchemy 2.0:** Async engine setup.
    - [x] **Schema Mapping:** Map Domain Entities to SQL Tables explicitly (Data Mapper pattern).
    - [x] **Alembic:** Init and create `0001_initial_structure` (Configured, waiting for DB).
    - [x] **Repository Impl:** Implement `SqlAlchemyUserRepository`.

- [x] **2.2. Vector Memory Adapter (`src/infra/vector`)**
    - [x] **Redis Adapter:** Implement `RedisMemoryService`.
    - [x] **Dual-Write Logic:** Ensure that when a Fact is "Saved", it goes to BOTH Postgres (Reliability) and Redis (Search).

---

## 🧠 Phase 3: The Agent "Brain" (Logic & Evals)
**Goal:** Create deterministic agent behavior with observability.

- [x] **3.1. Structured Prompts (`src/app/prompts`)**
    - [x] Use `Jinja2` or LangChain templates.
    - [x] **Versioning:** `architect_v1.j2`, `critic_v2.j2`.
    - [x] **Strict Structured Output:** Define Pydantic models for *every* LLM call (e.g., `PlanSchema`, `CritiqueSchema`).

- [x] **3.2. Circuit Breakers & Retries (`src/infra/llm`)**
    - [x] Implement a wrapper around LLM calls using `tenacity`.
    - [x] **Fallback:** If LLM fails 3 times, throw a custom `AgentServiceUnavailable` exception (don't crash the app).

- [x] **3.3. Unit Testing with Mocks**
    - [x] Test the "Interviewer" logic by mocking the LLM. Verify it handles "Silence" or "Garbage input" correctly without calling the real API.

---

## 🔄 Phase 4: Orchestration (LangGraph)
**Goal:** Stateful workflow management with persistence.

- [x] **4.1. The Graph State (`src/app/graph/state.py`)**
    - [x] Define `AgentState` using `TypedDict`. Include `error_count` and `retry_depth` for resilience.

- [x] **4.2. Workflow Definition**
    - [x] **Nodes:** Architect, Interviewer, Critic.
    - [x] **Conditional Edges:** Logic for `Critic -> (Approve) -> Interviewer` vs `Critic -> (Reject) -> Retry`.
    - [x] **Checkpointer:** Use `AsyncPostgresSaver`. This is crucial for "Long-running" conversations (days/weeks).

- [x] **4.3. LangFuse Integration**
    - [x] Add `@observe` decorators to the Graph entry point. Ensure input/output tokens are counted.

---

## 🔌 Phase 5: API Gateway (The Hexagon Boundary)
**Goal:** Expose the logic via HTTP.

- [x] **5.1. FastAPI Application**
    - [x] **Dependency Injection:** Inject `MemoryService` and `GraphRunnable` into routes using `Depends()`.
    - [x] **DTOs:** Create Request/Response Pydantic models (don't expose internal domain entities directly).

- [x] **5.2. Endpoints**
    - [x] `POST /v1/chat/message`: The main loop.
    - [x] `GET /v1/debug/state/{thread_id}`: Admin endpoint to see the current graph state (for debugging).

---

## 🤖 Phase 6: Async Client (Telegram)
**Goal:** A "dumb" terminal that strictly forwards messages.

- [x] **6.1. Webhook Handler**
    - [x] Do not put business logic here.
    - [x] **Queueing (Optional but Recommended):** Ideally, push updates to an internal memory queue if traffic is high, but direct API call is okay for MVP.
    - [x] **Formatting:** Convert Markdown from API to HTML for Telegram.

---

## 🧪 Phase 7: Persistent Checkpoints (Postgres)
**Goal:** Ensure resilience for long-running agent threads.
- [x] **7.1. Dependency Setup**
    - [x] Install `langgraph-checkpoint-postgres`.
    - [x] Configure connection pool in `lifespan`.
- [x] **7.2. Integration**
    - [x] Replace `MemorySaver` with `AsyncPostgresSaver`.
    - [x] Auto-create checkpoint tables on startup.

---

## 🔄 Phase 8: Graph Expansion (Critic Loop)
**Goal:** Implement self-correcting agentic behavior.
- [x] **8.1. Critic Agent**
    - [x] Implement `critic_node` with `CritiqueSchema`.
    - [x] "Approve" vs "Reject" logic.
- [x] **8.2. Cyclic Workflow**
    - [x] Conditional Edge: `Architect` <-> `Critic`.
    - [x] Circuit Breaker: Limit feedback loops to avoid infinite retries.

---

## 📚 Phase 9: Documentation & Polish
**Goal:** Handover-ready project.
- [x] **9.1. Documentation**
    - [x] `README.md` with Architecture Diagram (Mermaid).
    - [x] Run Instructions & API interactions.
- [x] **9.2. Verification**
    - [x] 100% Unit Test Pass Rate.
    - [x] Static Analysis (Ruff/Mypy) Clean.
