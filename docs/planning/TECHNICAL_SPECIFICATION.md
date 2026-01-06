# Technical Specification: Deep Profiling & Biography Agent System

## 1. System Goal
Develop an autonomous dialogue system for iterative collection of user biographical data through natural conversation. The system must manage long-term information gathering, breaking the process into sessions, validating response quality, and maintaining context.

## 2. Architecture & Stack
### Technology Stack
- **Orchestration**: LangChain, LangGraph (StateGraph).
- **Memory**: Mem0 (Local instance).
- **LLM Provider**: OpenRouter (Model agnostic).
- **Infrastructure**: Docker (All components containerized).
- **Database**: 
  - Internal storage for Mem0 (Vector Store).
  - LangGraph Checkpoints (Postgres/SQLite/Qdrant - local only).

### Key Data Requirements
- **Multi-tenancy**: Strict data isolation by `user_id`.
- **Raw Data**: Mem0 metadata must store raw "system question — user answer" pairs to prevent hallucinations during summarization.

## 3. Modular Structure & Roles
The system is implemented as a set of interacting agents with clear separation of concerns.

### 3.1. Communication Layer (Gateway)
- **Responsibility**: I/O Abstraction.
- **Current Implementation**: Telegram Bot API.
- **Functions**:
  - Receive messages from user.
  - Pass `user_id` and text to the system core.
  - Send text responses back to the user.
  - *Future proofing*: Architecture must support other channels (Voice, Web) without changing the core.

### 3.2. Architect (Global Planner)
- **Type**: High-Level State Machine.
- **Responsibility**: Long-term management of the biography collection process (outside specific session scope).
- **Functionality**:
  - **Spheres CRUD**: Manage topics (Childhood, Career, Education). Support presets and custom user topics.
  - **Plan Generation**: Create a list of "Biographical Points" to cover before starting a session on a selected sphere.
  - **Approval**: Send the plan to the user for confirmation or correction before starting the interview.
  - **Progress Analysis**: Decide if a sphere is fully covered or requires a new session.

### 3.3. "Interviewer + Critic" Tandem (Session Loop)
These roles work within a session as a unified mechanism (LangGraph Subgraph).

#### Agent-Interviewer
- **Responsibility**: Dialogue management, conversation tactics.
- **Functionality**:
  - Ask questions according to the plan approved by the Architect.
  - Maintain a "human" tone.
  - Decide when to stop the session (based on message limit, logical conclusion, or "stop" command).

#### Agent-Critic
- **Responsibility**: Quality Assurance & Validation.
- **Functionality**:
  - Analyze every user response *before* the Interviewer generates the next question.
  - **Checks**:
    - **Substance**: "Is this an answer or noise?"
    - **Completeness**: "Is the plan point covered?"
    - **Context**: "Is a follow-up question needed before moving to the next point?"
  - If the answer is incomplete/unclear, signal the Interviewer to "press" the topic further.

## 4. Workflow Scenarios

### Phase 1: Initialization & Planning (Architect)
1. User selects a Sphere (e.g., "Career 2010-2015").
2. Architect queries Mem0 to check what is already known.
3. Architect generates a **Draft Plan** (list of points to discuss).
4. User edits/confirms the plan.
5. System transitions to **Session Mode**.

### Phase 2: Interviewing (Interviewer + Critic Loop)
1. Interviewer asks a question regarding the first plan point.
2. User sends a message (short, broken, or transcribed voice).
3. Critic evaluates the message:
    - **Status: Insufficient** -> Interviewer asks for clarification.
    - **Status: Accepted** -> Data is effectively captured; Interviewer moves to the next point.
4. Process repeats until the plan is exhausted or user stops.

### Phase 3: Finalization (Memory Commit)
1. Raw dialogues and extracted facts are saved to Mem0.
2. Control returns to Architect to update global Sphere status ("In Progress" -> "Completed").

## 5. Definition of Done
- **Docker Compose**: Project starts with a single command `docker-compose up`.
- **Configuration**: All API keys (OpenRouter, Telegram) and DB paths are in `.env`.
- **Persistence**: LangGraph state (checkpoints) persists on disk to survive container restarts.
- **Local Memory**: Mem0 is configured for local vector storage (no cloud egress).
