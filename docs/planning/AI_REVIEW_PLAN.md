# AI Documentation Review Plan

## Objective
Systematically update all `*.md` files in the `agent-interview` project to strictly align with the **Agent Playbook** (`docs/planning/README.md`) and **Opencode Rules** (`.opencode/rules.md`).

**Primary Goal:** Optimize documentation for AI agent consumption by ensuring all files are:
1.  **Concise:** No fluff, no marketing, no roleplay.
2.  **Structured:** Use clear headers and bullet points.
3.  **Accurate:** Reflect `pyproject.toml` (Python 3.12+, strict typing) and current stack (LangGraph, Mem0).
4.  **Directive:** Provide clear instructions and invariants.

## Review Standards
- **Source of Truth:** `docs/planning/README.md` (The Agent Playbook).
- **Tone:** Imperative, technical, neutral.
- **Forbidden:** Narrative transitions ("In this section we will..."), future tense promises, ambiguity.
- **Dependency Check:** Verify all library mentions match `pyproject.toml` versions.

## Execution Sessions

### Session 1: The Brain (Rules & Playbook)
*Goal: Establish the absolute source of truth for all agents.*

**Target Files:**
- `.opencode/rules.md`
- `docs/planning/README.md`
- `README.md` (Root)

**Tasks:**
- [ ] **`.opencode/rules.md`**:
    - Ensure it explicitly points to `docs/planning/README.md` as the Playbook.
    - Define strict "AI Persona" rules (no chatting, just working).
- [ ] **`docs/planning/README.md`**:
    - Validate "Mission", "Workflow" (Summarizer -> Architect -> Critic -> Interviewer), and "Stack".
    - Ensure it forbids creation of `docs/archive` or split planning files.
- [ ] **`README.md`**:
    - Strip down to a minimal entry point.
    - Ensure "Quick Start" commands match `Makefile` or `uv` usage exactly.
    - Link **only** to the Agent Playbook for further reading.

### Session 2: The Body (Architecture)
*Goal: accurately map the system's static and dynamic structure.*

**Target Files:**
- `docs/ARCHITECTURE.md`
- `docs/architecture/CONTEXT.md`
- `docs/architecture/PATTERNS.md`
- `docs/architecture/DECISIONS.md`

**Tasks:**
- [ ] **`docs/ARCHITECTURE.md`**: Update high-level diagrams to reflect the current LangGraph nodes.
- [ ] **`docs/architecture/CONTEXT.md`**:
    - Update the **Repository Map** (file tree).
    - detailed list of **System Invariants** (e.g., "The Critic never edits memory directly").
- [ ] **`docs/architecture/PATTERNS.md`**:
    - Document the specific "Node Pattern" used in `src/app/graph/nodes`.
    - Document the "Prompt Engineering" approach (Jinja2 templates).
- [ ] **`docs/architecture/DECISIONS.md`**:
    - Verify ADRs exist for: LangGraph (Statefulness), Mem0 (Vector Memory), and Hexagonal Architecture.

### Session 3: The Skills (Guides & API)
*Goal: Provide executable instructions for developers and agents.*

**Target Files:**
- `docs/guides/CODING_STANDARDS.md`
- `docs/guides/TESTING.md`
- `docs/API.md`
- `TODO.md`
- `CHANGELOG.md`

**Tasks:**
- [ ] **`docs/guides/CODING_STANDARDS.md`**:
    - Hard-enforce `ruff` (line-length 88) and `mypy` (strict) settings from `pyproject.toml`.
    - Remove "suggestions"; replace with "requirements".
- [ ] **`docs/guides/TESTING.md`**:
    - specific `pytest` commands including async support.
    - Define the test pyramid for this project (Unit vs Integration).
- [ ] **`docs/API.md`**: Ensure endpoints match `src/entrypoints`.
- [ ] **`TODO.md`**: Clean up and align with the Roadmap in the Playbook.

## Verification Checklist
- [ ] **Link Integrity:** All relative links work.
- [ ] **Version Consistency:** Python 3.12+ mentioned consistently.
- [ ] **Voice Check:** No "marketing" or "conversational" filler.
