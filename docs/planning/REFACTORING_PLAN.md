# Refactoring Plan: Architecture V2 Implementation

This document outlines the step-by-step plan to transform the current codebase into the "Deep Profiling Agent System" defined in [TECHNICAL_SPECIFICATION.md](./TECHNICAL_SPECIFICATION.md).

## Phase 1: Infrastructure & Data Layer
**Goal**: Establish the storage foundation for Mem0 and Spheres.

### 1.1. Mem0 Integration
- [ ] **Dependency**: Add `mem0ai` to `pyproject.toml`.
- [ ] **Configuration**: Create `src/infra/mem0/client.py`.
    - Configure for **Local** usage (likely using Qdrant or Chroma locally).
    - Ensure `user_id` segregation is enforced in all calls.
- [ ] **Storage**: Ensure Docker Compose includes necessary vector DB service (or use embedded).

### 1.2. Domain Models (Spheres)
- [ ] **Schema**: Create `src/domain/entities/sphere.py`.
    - Fields: `id`, `user_id`, `name` (e.g., "Childhood"), `status` (Not Started, In Progress, Completed), `description`, `created_at`.
- [ ] **Database**: Create SQLAlchemy models in `src/infra/database/models/sphere.py`.
- [ ] **Repository**: Implement `SphereRepository` for CRUD operations.

## Phase 2: The Architect (Planner)
**Goal**: Enable the system to manage the high-level lifecycle of biography collection.

### 2.1. Spheres Management
- [ ] Create `Architect` tools/skills to:
    - List available spheres.
    - Create a new sphere/topic.
    - Select a sphere for the current session.

### 2.2. Plan Generation
- [ ] **Logic**:
    - Fetch existing memories from Mem0 for the user.
    - Generate a `SessionPlan` (list of questions/points) based on the selected Sphere.
    - **Prompting**: "Given what we know (Mem0) and the topic (Sphere), what should we ask next?"

### 2.3. User Interaction (Approval)
- [ ] Update `Architect` node to output a `PlanReview` state.
- [ ] The system must pause and wait for User text confirmation before proceeding to the Session Loop.

## Phase 3: The Session Loop (Interviewer + Critic)
**Goal**: Implement the core "Question -> Answer -> Critique" cycle.

### 3.1. Critic Agent (The Validator)
- [ ] **Refactoring**: Change `Critic` from "Plan Reviewer" to "Response Validator".
- [ ] **Input**: Current Plan Point + User's Last Message.
- [ ] **Output**: `ValidationResult` (Approved/Rejected, Reasoning, Hint for Interviewer).

### 3.2. Interviewer Agent (The conversationalist)
- [ ] **Logic**:
    - If starting: Ask question for Point N.
    - If Critic Rejected: Rephrase/Push based on Critic's hint.
    - If Critic Approved: Save fact to Mem0 -> Move to Point N+1.
- [ ] **Tools**: Give Interviewer access to `mem0.add(text, user_id=...)`.

### 3.3. Sub-Graph Design
- [ ] Redesign `workflow.py` to support the nested loop:
    ```mermaid
    graph LR
    Arch[Architect] -->|Plan| UserApprove
    UserApprove -->|Ok| Interviewer
    Interviewer --> User[User Input]
    User --> Critic
    Critic -->|Bad| Interviewer
    Critic -->|Good| Memory[Save & Next]
    Memory --> Interviewer
    ```

## Phase 4: Integration & Cleanup
**Goal**: Polish the user experience.

### 4.1. Telegram Gateway
- [ ] Ensure the bot correctly renders the "Plan" for approval.
- [ ] Handle "Stop" commands to gracefully exit the Session Loop and return to Architect.

### 4.2. Migration
- [ ] Clean up old nodes/prompts that are no longer relevant (e.g., old "Interviewer" logic that just chatted without structure).
