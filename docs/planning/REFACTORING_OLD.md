# 🔧 REFACTORING PLAN

> **Generated**: 2026-01-06  
> **Last Updated**: 2026-01-06 23:25  
> **Focus**: Architecture improvements, code quality, and maintainability  
> **Approach**: Incremental refactoring with backward compatibility  
> **Progress**: 2/9 actions completed (✅ RA-001, ✅ RA-002)

---

## 🎯 Refactoring Objectives

1. **Strengthen Hexagonal Architecture**: Eliminate remaining layer violations
2. **Improve Testability**: Make components easier to test in isolation
3. **Enhance Dependency Injection**: Make dependencies explicit and configurable
4. **Reduce Coupling**: Minimize module interdependencies
5. **Improve Code Reusability**: Extract common patterns

---

## 📋 Phase 1: Domain Layer Hardening (Priority: Critical)

### RA-001: Create Domain Exception Hierarchy ✅ **COMPLETED**

**Current Issue**:
- Generic exceptions used throughout
- No mapping between domain errors and HTTP statuses
- Difficult to distinguish business rule violations from infrastructure failures

**Refactoring Steps**:

1. **Create Exception Hierarchy**
```python
# src/domain/exceptions.py (NEW FILE)
class DomainError(Exception):
    """Base class for all domain errors."""
    pass

class ResourceNotFound(DomainError):
    """Entity not found (maps to HTTP 404)."""
    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(f"{resource_type} with id '{identifier}' not found")

class BusinessRuleViolation(DomainError):
    """Business rule violated (maps to HTTP 400/409)."""
    pass

class UserNotFoundError(ResourceNotFound):
    def __init__(self, user_id: str):
        super().__init__("User", user_id)

class MemoryNotFoundError(ResourceNotFound):
    def __init__(self, memory_id: str):
        super().__init__("Memory", memory_id)

class InvalidEmailDomainError(BusinessRuleViolation):
    pass
```

2. **Update Domain Entities to Use Typed Exceptions**
```python
# src/domain/entities/user.py
# BEFORE:
raise ValueError("Disposable emails are forbidden.")

# AFTER:
from src.domain.exceptions import InvalidEmailDomainError
raise InvalidEmailDomainError(f"Email domain not allowed: {v}")
```

3. **Create FastAPI Exception Handlers**
```python
# src/entrypoints/api/error_handlers.py (NEW FILE)
from fastapi import Request
from fastapi.responses import JSONResponse
from src.domain.exceptions import ResourceNotFound, BusinessRuleViolation

async def resource_not_found_handler(request: Request, exc: ResourceNotFound):
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "resource": exc.resource_type,
            "identifier": exc.identifier,
        }
    )

async def business_rule_violation_handler(request: Request, exc: BusinessRuleViolation):
    return JSONResponse(
        status_code=400,
        content={"error": "business_rule_violation", "detail": str(exc)}
    )
```

4. **Register Handlers in Main**
```python
# src/main.py
from src.entrypoints.api.error_handlers import (
    resource_not_found_handler,
    business_rule_violation_handler,
)
app.add_exception_handler(ResourceNotFound, resource_not_found_handler)
app.add_exception_handler(BusinessRuleViolation, business_rule_violation_handler)
```

**Files Modified**: ✅ ALL COMPLETED
- ✅ `src/domain/exceptions.py` (created)
- ✅ `src/domain/entities/user.py` 
- ✅ `src/entrypoints/api/error_handlers.py` (created)
- ✅ `src/infra/llm/client.py` (added LLM exceptions)
- ✅ `src/main.py`

**Tests Added**: ✅
- ✅ `tests/unit/domain/test_exceptions.py`
- ✅ `tests/unit/entrypoints/test_api_routes.py` (error handling tests)

**Impact**: ⭐⭐⭐⭐⭐ Critical for production readiness - **ACHIEVED**

**Completion Date**: 2026-01-06

---

## 📋 Phase 2: Application Layer Refactoring (Priority: High)

### RA-002: Extract Prompt Management System ✅ **COMPLETED**

**Current Issue**:
- Prompts are hardcoded strings scattered across nodes
- No versioning or A/B testing capability
- Difficult to iterate on prompt engineering

**Refactoring Steps**:

1. **Create Prompt Templates**
```jinja2
{# src/app/prompts/critic_v1.j2 #}
You are the Critic, a quality assurance agent for an AI coaching system.

**Your Task**:
Review the plan created by the Architect and determine if it's ready for execution.

**Plan to Review**:
{{ plan_json }}

**Evaluation Criteria**:
1. Clarity: Are the steps clear and actionable?
2. Completeness: Does it address the user's goal?
3. Feasibility: Can the Interviewer execute this plan?

**Output Format** (strict JSON):
{
  "is_approved": boolean,
  "feedback": "string (specific suggestions)",
  "score": integer (1-10)
}
```

2. **Create Prompt Renderer Utility**
```python
# src/app/prompts/renderer.py (NEW FILE)
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Any

class PromptRenderer:
    def __init__(self, templates_dir: Path | str = "src/app/prompts"):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    
    def render(self, template_name: str, **context: Any) -> str:
        """Render a prompt template with the given context."""
        template = self.env.get_template(template_name)
        return template.render(**context)

# Global instance
prompt_renderer = PromptRenderer()
```

3. **Refactor Graph Nodes to Use Templates**
```python
# src/app/graph/nodes/critic.py
# BEFORE:
critique = await llm_client.generate(
    system_prompt="You are a Critic. Review the plan...",
    messages=messages,
    schema=CritiqueSchema,
)

# AFTER:
from src.app.prompts.renderer import prompt_renderer

system_prompt = prompt_renderer.render(
    "critic_v1.j2",
    plan_json=state["plan"].model_dump_json(indent=2)
)
critique = await llm_client.generate(
    system_prompt=system_prompt,
    messages=messages,
    schema=CritiqueSchema,
)
```

**Files Modified**: ✅ ALL COMPLETED
- ✅ `src/app/prompts/critic.j2` (created)
- ✅ `src/app/prompts/interviewer.j2` (created)
- ✅ `src/app/prompts/renderer.py` (created)
- ✅ `src/app/graph/nodes/architect.py`
- ✅ `src/app/graph/nodes/critic.py`
- ✅ `src/app/graph/nodes/interviewer.py`

**Tests Added**: ✅
- ✅ `tests/unit/app/prompts/test_template_rendering.py` (expanded)
- ✅ `tests/unit/app/prompts/test_renderer.py` (new)

**Impact**: ⭐⭐⭐⭐ High - Enables rapid prompt iteration - **ACHIEVED**

**Completion Date**: 2026-01-06

---

### RA-003: Implement Dependency Injection for Graph Nodes

**Current Issue**:
- Graph nodes use global singletons (`llm_client = get_llm_client()`)
- Cannot inject different implementations for testing
- Cannot access DB sessions or other services

**Refactoring Steps**:

1. **Define Node Dependencies Interface**
```python
# src/app/graph/dependencies.py (NEW FILE)
from dataclasses import dataclass
from src.domain.ports.llm_provider import LLMProviderProtocol
from src.domain.ports.user_repository import UserRepositoryProtocol
from src.domain.ports.memory_service import MemoryServiceProtocol

@dataclass
class GraphDependencies:
    """Container for all graph node dependencies."""
    llm: LLMProviderProtocol
    user_repo: UserRepositoryProtocol
    memory_service: MemoryServiceProtocol
```

2. **Update Node Signatures to Accept Dependencies**
```python
# src/app/graph/nodes/architect.py
# BEFORE:
llm_client = get_llm_client()

async def architect_node(state: AgentState) -> dict[str, Any]:
    plan = await llm_client.generate(...)

# AFTER:
async def architect_node(
    state: AgentState,
    deps: GraphDependencies,
) -> dict[str, Any]:
    plan = await deps.llm.generate(...)
```

3. **Create Dependency Factory**
```python
# src/app/dependencies.py
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from src.app.graph.dependencies import GraphDependencies
from src.infra.llm.client import get_llm_client
from src.infra.db.repositories.user_repo import SqlAlchemyUserRepository
from src.infra.vector.memory import RedisMemoryService

async def create_graph_dependencies(
    session: AsyncSession,
    redis: Redis,
) -> GraphDependencies:
    return GraphDependencies(
        llm=get_llm_client(),
        user_repo=SqlAlchemyUserRepository(session),
        memory_service=RedisMemoryService(redis),
    )
```

4. **Bind Dependencies in Workflow Compilation**
```python
# src/app/graph/workflow.py
from functools import partial

def create_graph(checkpointer: Any, dependencies: GraphDependencies) -> Any:
    workflow = StateGraph(AgentState)
    
    # Bind dependencies using partial application
    workflow.add_node("architect", partial(architect_node, deps=dependencies))
    workflow.add_node("critic", partial(critic_node, deps=dependencies))
    workflow.add_node("interviewer", partial(interviewer_node, deps=dependencies))
    
    # ... rest of workflow setup
    return workflow.compile(checkpointer=checkpointer)
```

**Files Modified**:
- `src/app/graph/dependencies.py` (new)
- `src/app/dependencies.py`
- `src/app/graph/nodes/*.py` (all nodes)
- `src/app/graph/workflow.py`
- `src/main.py` (update graph creation)

**Tests Impact**:
- Makes all node tests 100% mockable
- No more global state in tests

**Impact**: ⭐⭐⭐⭐⭐ Critical for testability

---

### RA-004: Extract State Management Logic

**Current Issue**:
- `AgentState` is a raw TypedDict with no behavior
- No encapsulation of state transitions
- Difficult to add validation or history tracking

**Refactoring Steps**:

1. **Create State Manager Class**
```python
# src/app/graph/state_manager.py (NEW FILE)
from typing import Any
from src.app.graph.state import AgentState
from src.app.schemas import PlanSchema, CritiqueSchema

class StateManager:
    """Encapsulates state transitions and validation."""
    
    def __init__(self, state: AgentState):
        self._state = state
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self._state["messages"].append({"role": role, "content": content})
    
    def update_plan(self, plan: PlanSchema) -> None:
        """Update the current plan."""
        self._state["plan"] = plan
    
    def update_critique(self, critique: CritiqueSchema) -> None:
        """Update the current critique."""
        self._state["critique"] = critique
    
    def increment_step(self) -> None:
        """Increment step counter."""
        self._state["step_count"] += 1
    
    def should_retry_architect(self) -> bool:
        """Determine if we should send back to architect."""
        critique = self._state.get("critique")
        if not critique:
            return False
        
        if critique.is_approved:
            return False
        
        # Circuit breaker: max 5 iterations
        return self._state["step_count"] < 5
    
    def get_state(self) -> AgentState:
        """Get the raw state dictionary."""
        return self._state
```

2. **Refactor Nodes to Use State Manager**
```python
# src/app/graph/nodes/architect.py
async def architect_node(
    state: AgentState,
    deps: GraphDependencies,
) -> dict[str, Any]:
    manager = StateManager(state)
    
    plan = await deps.llm.generate(...)
    
    manager.update_plan(plan)
    manager.increment_step()
    
    return manager.get_state()
```

**Files Modified**:
- `src/app/graph/state_manager.py` (new)
- `src/app/graph/nodes/*.py` (all nodes)
- `src/app/graph/workflow.py` (use in `should_continue`)

**Impact**: ⭐⭐⭐ Medium-High - Improves maintainability

---

## 📋 Phase 3: Infrastructure Layer Optimization (Priority: Medium)

### RA-005: Consolidate Database Session Management

**Current Issue**:
- No clear session lifecycle management
- Potential for session leaks
- No transaction boundary control

**Refactoring Steps**:

1. **Create Session Context Manager**
```python
# src/infra/db/session.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.settings import settings

engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """Provide a transactional scope for database operations."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

2. **Update Repository Pattern with Unit of Work**
```python
# src/infra/db/unit_of_work.py (NEW FILE)
from contextlib import asynccontextmanager
from src.infra.db.session import get_db_session
from src.infra.db.repositories.user_repo import SqlAlchemyUserRepository

class UnitOfWork:
    """Manages a database session and repositories."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = SqlAlchemyUserRepository(session)
    
    async def commit(self) -> None:
        await self.session.commit()
    
    async def rollback(self) -> None:
        await self.session.rollback()

@asynccontextmanager
async def get_unit_of_work():
    async with get_db_session() as session:
        yield UnitOfWork(session)
```

**Files Modified**:
- `src/infra/db/session.py`
- `src/infra/db/unit_of_work.py` (new)
- All places using repositories

**Impact**: ⭐⭐⭐⭐ High - Prevents transaction bugs

---

### RA-006: Refactor LLM Client Message Handling

**Current Issue**:
- `_convert_messages` has too many fallbacks
- Type hints use `Any` instead of specific types
- Error handling is silent (catches all exceptions)

**Refactoring Steps**:

1. **Define Message Protocol**
```python
# src/infra/llm/messages.py (NEW FILE)
from typing import Protocol, Literal
from pydantic import BaseModel

MessageRole = Literal["system", "user", "assistant", "tool"]

class Message(BaseModel):
    """Standardized message format."""
    role: MessageRole
    content: str

class MessageConverter(Protocol):
    """Interface for converting various message formats."""
    
    def to_openai_format(self, messages: list[Any]) -> list[dict[str, str]]:
        """Convert to OpenAI API format."""
        ...
```

2. **Implement Strict Converter**
```python
# src/infra/llm/messages.py
from typing import Any

class StrictMessageConverter:
    """Converts messages with strict validation."""
    
    def to_openai_format(self, messages: list[Any]) -> list[dict[str, str]]:
        """Convert messages to OpenAI format."""
        result = []
        
        for msg in messages:
            if isinstance(msg, dict):
                # Validate dict has required keys
                if "role" not in msg or "content" not in msg:
                    raise ValueError(f"Invalid message dict: {msg}")
                result.append(msg)
            
            elif isinstance(msg, Message):
                result.append(msg.model_dump())
            
            elif hasattr(msg, "type") and hasattr(msg, "content"):
                # LangChain message
                role = self._convert_langchain_role(msg.type)
                result.append({"role": role, "content": str(msg.content)})
            
            else:
                raise TypeError(f"Unsupported message type: {type(msg)}")
        
        return result
    
    def _convert_langchain_role(self, lc_type: str) -> MessageRole:
        """Convert LangChain message type to OpenAI role."""
        mapping = {
            "human": "user",
            "ai": "assistant",
            "system": "system",
            "tool": "tool",
        }
        if lc_type not in mapping:
            raise ValueError(f"Unknown LangChain message type: {lc_type}")
        return mapping[lc_type]
```

3. **Update LLM Client**
```python
# src/infra/llm/client.py
class OpenAIClient(LLMProviderProtocol):
    def __init__(self):
        self.client = AsyncOpenAI(...)
        self.model = settings.MODEL_NAME
        self.converter = StrictMessageConverter()  # NEW
    
    async def generate_text(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> str:
        # Use converter instead of _convert_messages
        clean_messages = self.converter.to_openai_format(messages)
        msgs = [{"role": "system", "content": system_prompt}] + clean_messages
        # ... rest of method
```

**Files Modified**:
- `src/infra/llm/messages.py` (new)
- `src/infra/llm/client.py`

**Tests to Add**:
- `tests/unit/infra/test_message_converter.py`

**Impact**: ⭐⭐⭐ Medium - Better error messages

---

## 📋 Phase 4: API Layer Improvements (Priority: Medium)

### RA-007: Implement Proper DTOs (Data Transfer Objects)

**Current Issue**:
- API returns raw internal state
- No separation between internal and external models
- Breaks encapsulation

**Refactoring Steps**:

1. **Create API DTOs**
```python
# src/entrypoints/api/schemas.py (NEW FILE)
from pydantic import BaseModel, Field
from uuid import UUID

# Request DTOs
class ChatMessageRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=5000)
    thread_id: str = Field(default="default_thread", min_length=1)

# Response DTOs
class ChatMessageResponse(BaseModel):
    response: str
    step_count: int
    thread_id: str
    
    class Config:
        from_attributes = True

class ThreadStateResponse(BaseModel):
    """External view of thread state (hides internals)."""
    thread_id: str
    message_count: int
    last_agent: str
    has_plan: bool
    plan_summary: str | None = None
    
    @classmethod
    def from_state(cls, thread_id: str, state: dict) -> "ThreadStateResponse":
        plan = state.get("plan")
        return cls(
            thread_id=thread_id,
            message_count=len(state.get("messages", [])),
            last_agent=state.get("last_agent", "unknown"),
            has_plan=plan is not None,
            plan_summary=plan.goal_analysis if plan else None,
        )
```

2. **Update Router to Use DTOs**
```python
# src/entrypoints/api/router.py
from src.entrypoints.api.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ThreadStateResponse,
)

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,  # Use DTO
    graph: Any = Depends(get_graph),
) -> ChatMessageResponse:
    # ... execute graph ...
    
    return ChatMessageResponse(
        response=str(content),
        step_count=final_state.get("step_count", 0),
        thread_id=request.thread_id,
    )

@router.get("/debug/state/{thread_id}", response_model=ThreadStateResponse)
async def get_state(
    thread_id: str,
    graph: Any = Depends(get_graph),
) -> ThreadStateResponse:
    state_snapshot = await graph.aget_state(config)
    return ThreadStateResponse.from_state(thread_id, dict(state_snapshot.values))
```

**Files Modified**:
- `src/entrypoints/api/schemas.py` (new)
- `src/entrypoints/api/router.py`

**Impact**: ⭐⭐⭐⭐ High - Production best practice

---

## 📋 Phase 5: Code Quality & Standards (Priority: Low)

### RA-008: Remove Code Duplication

**Current Issue**:
- Line 33 in `workflow.py` duplicates line 32

**Refactoring Steps**:
```python
# src/app/graph/workflow.py
# BEFORE (lines 32-33):
workflow = StateGraph(AgentState)
workflow = StateGraph(AgentState)  # DUPLICATE

# AFTER (line 32):
workflow = StateGraph(AgentState)
```

**Files Modified**:
- `src/app/graph/workflow.py`

**Impact**: ⭐ Low - Minor cleanup

---

### RA-009: Extract Configuration Constants

**Current Issue**:
- Magic numbers scattered in code (e.g., `step_count > 5`)
- No central place for tuning thresholds

**Refactoring Steps**:

1. **Create Constants File**
```python
# src/app/config.py (NEW FILE)
"""Application-level configuration constants."""

# Graph Workflow
MAX_ARCHITECT_RETRIES = 5
MAX_MESSAGE_HISTORY = 20
CONVERSATION_SUMMARY_THRESHOLD = 15

# LLM Settings
DEFAULT_TEMPERATURE = 0.7
MAX_TOKENS_PER_RESPONSE = 2000

# Memory Management
MEMORY_IMPORTANCE_THRESHOLD = 7
MAX_MEMORIES_PER_QUERY = 10
```

2. **Use Constants in Code**
```python
# src/app/graph/workflow.py
from src.app.config import MAX_ARCHITECT_RETRIES

def should_continue(state: AgentState) -> str:
    # BEFORE: if state.get("step_count", 0) > 5:
    # AFTER:
    if state.get("step_count", 0) > MAX_ARCHITECT_RETRIES:
        return "interviewer"
```

**Files Modified**:
- `src/app/config.py` (new)
- `src/app/graph/workflow.py`
- Various other files using magic numbers

**Impact**: ⭐⭐ Low-Medium - Easier tuning

---

## 📊 Refactoring Execution Plan

### Recommended Order:

1. **Week 1**: Phase 1 (RA-001) - Domain exceptions
2. **Week 2**: Phase 2 (RA-002, RA-003) - Prompts & DI
3. **Week 3**: Phase 2 (RA-004) + Phase 3 (RA-005) - State management & DB
4. **Week 4**: Phase 3 (RA-006) + Phase 4 (RA-007) - LLM client & DTOs
5. **Week 5**: Phase 5 (RA-008, RA-009) - Cleanup

### Testing Strategy for Each Phase:

- ✅ All existing tests must pass after refactoring
- ✅ Add new tests for refactored components
- ✅ Run full E2E test suite after each phase
- ✅ Verify linters (Ruff, Mypy) still pass

### Rollback Plan:

- Git branch per refactoring phase
- Feature flags for major changes
- Keep old code commented for 1 sprint

---

## 🎯 Success Metrics

**Code Quality**:
- [x] Mypy strict: 0 errors (\u2705 **ACHIEVED**)
- [x] Ruff: 0 violations (\u2705 **ACHIEVED**)
- [x] Test coverage: All tests passing (40/40) (\u2705 **ACHIEVED**)
- [ ] Test coverage: >85% (current: estimate 70-80%)
- [ ] Cyclomatic complexity: <10 per function

**Maintainability**:
- [x] Domain exception hierarchy: Complete (\u2705 **ACHIEVED**)
- [x] Prompt externalization: Complete (\u2705 **ACHIEVED**)
- [ ] SOLID violations: 0
- [ ] Circular dependencies: 0
- [ ] Layer violations: 0 (domain imports infra)

**Performance**:
- [ ] API latency: <500ms (p95)
- [ ] Database connection pool: <50% utilization
- [ ] Memory leaks: 0

**Progress**: 2/9 refactoring actions completed (22%)

---

## 📚 References

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design - Eric Evans](https://www.domainlanguage.com/ddd/)
