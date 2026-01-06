# Project Roadmap

## 📍 Current Focus: Architecture V2 Overhaul

We are currently transitioning the system to the **Deep Profiling & Biography Agent** architecture.

### Phase 1: Planning & Documentation (✅ Completed)
- [x] Translation of Requirements to Technical Spec.
- [x] Creation of Refactoring Plan.

### Phase 2: Core Infrastructure & Data Layer (🚧 Next Up)
- [ ] **Mem0 Integration**: Setup local vector store and `mem0ai` client.
- [ ] **Spheres Module**: Model design and Database Logic (SQLAlchemy) for managing separate biography topics.
- [ ] **Data Model Update**: Enforce multi-tenancy (`user_id`) across all storage.

### Phase 3: The Architect Agent
- [ ] **Plan Generation**: Implement logic to generating interview plans from `Mem0` context.
- [ ] **Spheres Management**: Tools for creating/selecting spheres.
- [ ] **User Feedback**: Implement "Plan Approval" state.

### Phase 4: Session Loop (Interviewer + Critic)
- [ ] **Critic Agent Refactoring**: Switch from "Plan Review" to "Response Validation".
- [ ] **Interviewer Logic**: Implement plan-following dialogue.
- [ ] **Graph Redesign**: Implement the nested `Architect -> Session Loop` workflow.

### Phase 5: Polish & Verify
- [ ] **Telegram Integration**: Support for approval buttons and new workflow states.
- [ ] **End-to-End Testing**: Verify a full session from Sphere selection to Fact storage.

---

## 🔮 Future / Backlog
- **Voice Interface**: Audio input/output support.
- **Web Interface**: React/Next.js frontend for managing spheres and viewing gathered biography.
- **Analysis Module**: generating "Life Story" summaries from collected facts.
