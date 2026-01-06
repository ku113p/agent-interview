# Deep Profiling & Biography Agent System

## 🚀 Abstract
This project implements an **Autonomous Dialogue System** designed for deeply profiling users and collecting their biographies through natural conversation. 

Built with **Python 3.14**, **LangGraph**, and **Mem0**, it features an intelligent agent team that plans interviews, validates answers in real-time, and builds a structured knowledge base of the user's life events.

> **Key Capabilities:**
> - **Long-term Memory:** Uses `Mem0` to remember facts across sessions.
> - **Structured Planning:** The **Architect** agent plans interview sessions by topics (Spheres).
> - **Self-Correction:** The **Critic** agent validates user answers to ensure quality data collection.
> - **Multi-Tenancy:** Strict data isolation by user ID.

## 🛠️ Technology Stack
- **Language:** Python 3.14 (managed by `uv`)
- **Orchestration:** LangChain, LangGraph (Stateful Agents)
- **Memory:** Mem0 (Local Vector Store)
- **Database:** PostgreSQL/SQLite (Checkpoints & App Data)
- **Interface:** Telegram Bot API
- **Infrastructure:** Docker (Fully containerized)

## 🏗️ Architecture
The system operates using a role-based agent workflow:

1.  **Gateway (Telegram):** Handles user I/O.
2.  **Architect (Global Planner):**
    -   Manages "Spheres" of life (Childhood, Career, etc.).
    -   Generates interview plans based on existing memory.
    -   Tracks global progress.
3.  **Session Loop (Interviewer + Critic):**
    -   **Interviewer:** Conducts the dialogue based on the Architect's plan.
    -   **Critic:** Validates every user answer for completeness and clarity *before* the conversation moves on.

```mermaid
graph TD
    User((User)) <-->|Telegram| Gateway
    Gateway <--> Arch[Architect]
    Arch <-->|Read/Write| Mem0[(Mem0 Memory)]
    Arch -->|Plan| Session[Session Loop]
    subgraph "Session Loop"
        Interviewer <--> Critic
    end
    Session -->|New Facts| Mem0
```

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- `uv` Package Manager

### 1. Initialize Environment
```bash
uv sync
```

### 2. Configure
Copy `.env.example` to `.env` and set your API keys (OpenRouter, Telegram).

### 3. Start System
```bash
docker-compose up -d
```

## 📂 Project Structure
```
src/
├── app/            
│   ├── graph/      # LangGraph Workflows (Architect, Interviewer, Critic)
│   └── nodes/      # Agent implementations
├── domain/         # Entities (Sphere, Plan, Profile)
├── infra/          # Adapters (Mem0, DB, Telegram)
└── main.py         # Entrypoint
```

## 📚 Documentation
- **Specs**: [Technical Specification](docs/planning/TECHNICAL_SPECIFICATION.md)
- **Plan**: [Refactoring Plan](docs/planning/REFACTORING_PLAN.md)
- **Roadmap**: [Roadmap](docs/planning/ROADMAP.md)
