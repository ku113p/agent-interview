# Project Tasks & Roadmap

**Source of Truth:** `docs/planning/README.md` (Agent Playbook).
**Status:** Implementation Phase.

## 🟢 Active Tasks (Infrastructure & Domain)
- [ ] **Infrastructure Setup**:
- [x] Verify `docker-compose.yml` for Postgres/Redis/LangFuse.
    - [ ] Run `alembic` migrations for initial schema.
- [ ] **Domain Core**:
    - [ ] Verify `UserProfile` and `Sphere` entities match strict Pydantic V2 rules.
    - [ ] Implement `Memory` entity logic.

## 🟡 Next Steps (Agent Implementation)
- [ ] **Agent Graph**:
    - [ ] Implement `Summarizer` node logic.
    - [ ] Implement `Architect` node logic (Prompt Engineering).
    - [ ] Implement `Critic` node logic.
    - [ ] Implement `Interviewer` node logic.

## 🔴 Future / Backlog
- [ ] **Telegram Integration**: Full webhook support.
- [ ] **Voice Interface**: Audio-to-text input.
- [ ] **Admin Dashboard**: Web UI for monitoring interviews.
