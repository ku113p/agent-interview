# Project Context Map & Directory Structure

> **System:** Modular Agentic Monolith
> **Architecture:** Hexagonal (Ports & Adapters)
> **Stack:** Python 3.12, uv, FastAPI, Postgres, Redis.

**AI AGENT INSTRUCTION:** Review this map before creating files.

---

## 📂 High-Level Structure

```text
/
├── pyproject.toml         # uv managed dependencies
├── compose.yaml           # Postgres, Redis, LangFuse, Prometheus
├── src/
│   ├── domain/            # 🟢 PURE PYTHON. No DB/API imports.
│   ├── app/               # 🟡 ORCHESTRATION. LangGraph, Prompts.
│   ├── infra/             # 🔴 ADAPTERS. SQL, Redis, OpenAI.
│   ├── entrypoints/       # 🟣 DELIVERY. FastAPI, CLI.
│   └── main.py
└── tests/
```

## 🏗 Detailed Responsibilities

### 1. 🟢 `src/domain` (The Core)

* **`entities/`**: `UserProfile` (Pydantic). Strict validation.
* **`ports/`**: Protocols (`UserRepositoryProtocol`).
* **`events.py`**: Domain events (e.g., `MemoryCreated`) for the Outbox pattern.

### 2. 🟡 `src/app` (The Brain)

* **`graph/`**: `state.py` (TypedDict), `nodes/` (Architect, Interviewer).
* **`services/`**: Bridges Domain and Ports.
* **`prompts/`**: Jinja2 templates.

### 3. 🔴 `src/infra` (The Adapters)

* **`db/`**: SQLAlchemy 2.0 Async.
* `repositories/`: SqlAlchemy implementations.
* `outbox.py`: Worker to sync Postgres -> Redis.
* **`vector/`**: Redis client for semantic search.
* **`monitoring/`**: LangFuse tracing & Prometheus metrics.

### 4. 🟣 `src/entrypoints`

* **`api/`**: FastAPI routes.
* `dependencies.py`: DI Container.
* **`telegram/`**: Webhook handlers.

## 🚫 Critical Rules

1. **Domain Isolation:** `domain` imports NOTHING from `infra` or `app`.
2. **No Logic in Routes:** Controllers only parse JSON and call Services.
3. **Strict Typing:** All function signatures must be fully typed.
