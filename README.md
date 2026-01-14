# Agent Interview System

An autonomous biography-collection agent system powered by **LangGraph** (memory refactor in progress).

## 🚀 Quick Start

### 1. Initialize
```bash
uv sync
```

### 2. Run
```bash
docker-compose up -d app-db redis minio langfuse langfuse-db
```

> First run? Enable pgvector (`CREATE EXTENSION IF NOT EXISTS vector;`) and create the MinIO bucket (`mc mb minio/raw-interactions`). See docs/architecture/DECISIONS.md.

## 📚 Documentation

The complete system documentation and **Agent Playbook** are located here:

👉 **[docs/planning/README.md](docs/planning/README.md)**

*Refer to the Playbook for Architecture, Workflow, and Development Standards.*
