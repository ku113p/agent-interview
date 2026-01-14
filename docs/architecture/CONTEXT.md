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
├── docker-compose.yml     # Postgres, Redis, LangFuse, Prometheus
├── src/
│   ├── app/               # 🟡 ORCHESTRATION. LangGraph, Prompts, App Services.
│   │   ├── graph/         # State Machine (Nodes, Workflow).
│   │   ├── prompts/       # Jinja2 Templates.
│   │   └── services/      # Domain-App Bridge (ContextManager).
│   ├── domain/            # 🟢 PURE PYTHON. Entities, Ports.
│   ├── entrypoints/       # 🟣 DELIVERY. FastAPI, Telegram.
│   ├── infra/             # 🔴 ADAPTERS. SQL, Redis, OpenAI, MinIO.
│   ├── middleware/        # Correlation, Rate Limiting.
│   ├── services/          # Global Utilities (CostTracker).
│   ├── logging.py         # Structlog Configuration.
│   ├── main.py            # App Entrypoint.
│   └── settings.py        # Config & Env Vars.
└── tests/
```

## 🏗 Detailed Responsibilities

### 1. 🟢 `src/domain` (The Core)
*   **`entities/`**: `UserProfile`, `Sphere`, `Memory` (Pydantic). Strict validation.
*   **`ports/`**: Protocols (`UserRepositoryProtocol`, `SphereRepositoryProtocol`).
*   **`exceptions.py`**: Domain error hierarchy.

### 2. 🟡 `src/app` (The Brain)
*   **`graph/`**:
    *   `state.py`: `AgentState` TypedDict.
    *   `nodes/`: Agent implementations (`Architect`, `Critic`, `Interviewer`, `Summarizer`).
    *   `workflow.py`: Graph topology and conditional edges.
*   **`prompts/`**: Jinja2 templates (`.j2`) and `renderer.py`.
*   **`services/`**: Application services like `ContextManager`.

### 3. 🔴 `src/infra` (The Adapters)
*   **`db/`**: SQLAlchemy 2.0 Async (Models, Repositories, Migrations).
*   **`llm/`**: OpenAI Client wrapper.
*   **`storage/`**: MinIO adapters for raw payload retention.
*   **`security/`**: Content sanitization.

### 4. 🟣 `src/entrypoints`
*   **`api/`**: FastAPI routes (Routers, Schemas).
*   **`telegram/`**: Webhook handlers.

## 🚫 System Invariants & Critical Rules

1.  **Domain Isolation**: `domain` imports NOTHING from `infra`, `app`, or `entrypoints`.
2.  **Critic Isolation**: The **Critic** node never edits memory or DB directly. It only critiques the Architect's plan.
3.  **IO Boundary**: All external input/output must go through `entrypoints`. No deep linking into `src/app`.
4.  **State Persistence**: `AgentState` is the ONLY mechanism for passing data between nodes.
5.  **Strict Typing**: All function signatures must be fully typed.
