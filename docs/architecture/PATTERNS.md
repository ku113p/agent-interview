# Patterns

Each pattern below is a precise reminder for agents and humans about how the code must behave. Keep these summaries short, factual, and actionable.

---

## 1. Domain Layer
- Location: `src/domain/*` (entities, ports, events).
- Rule: Zero imports from infra, app, or entrypoints. Models must be pure Pydantic V2.
- Agents: Trust these models for validation and business invariants.

---

## 2. Ports (Protocols)
- Define contracts (e.g., `UserRepositoryProtocol`, `LLMProviderProtocol`) and nothing else.
- Infra implements the protocols; graph logic depends on them, not concrete classes.

---

## 3. Application Services & Graph Nodes
- Services: orchestrate domain + ports; no SQL or network directly.
- Graph nodes (Architect, Interviewer, Critic, Summarizer) run in `LangGraph.StateGraph` with fixed input/output schemas.
- Always validate prompt output with typed responses before updating state.

---

## 4. Prompts
- Stored as Jinja2 templates under `src/app/prompts/*.j2`.
- Each template renders into a Pydantic schema (Plan, Critique, Response).
- Version templates via filenames (e.g., `architect_v1.j2`).

---

## 5. Testing
- Unit tests mock protocols and run in memory (`tests/unit/`).
- Integration smoke tests (future) should spin up Postgres + Redis via `docker-compose`.
- Always add `pytest.mark.asyncio` for async logic.


**Location:** `src/domain/ports/`
**Rule:** Use `Protocol` for duck typing. Defines *what* we need, not *how* it works.

```python
from typing import Protocol
from uuid import UUID
from src.domain.entities.user import UserProfile

class UserRepositoryProtocol(Protocol):
    """
    Interface for User persistence.
    Infra layer MUST implement this.
    """
    
    async def get_by_id(self, user_id: UUID) -> Optional[UserProfile]:
        """Fetch user or return None."""
        ...

    async def save(self, user: UserProfile) -> None:
        """Persist the aggregate state."""
        ...

```

---

## 3. 🔴 The Adapter (The Infrastructure)

**Location:** `src/infra/db/repositories/`
**Rule:** Separation of concerns. SQL Models  Domain Models. Map explicitly. Use Async SQLAlchemy 2.0.

```python
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import Domain
from src.domain.entities.user import UserProfile
from src.domain.ports.user_repository import UserRepositoryProtocol

# Import Infra (SQL Model)
from src.infra.db.models import UserTable  

class SqlAlchemyUserRepository(UserRepositoryProtocol):
    """
    Implementation of the Port using Postgres.
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> Optional[UserProfile]:
        query = select(UserTable).where(UserTable.id == user_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        
        if not row:
            return None
            
        # MAPPER: SQL -> Domain (Explicit is better than implicit)
        return UserProfile(
            id=row.id,
            email=row.email,
            is_active=row.is_active,
            created_at=row.created_at
        )

    async def save(self, user: UserProfile) -> None:
        # MAPPER: Domain -> SQL
        # Using merge to handle both insert and update (Upsert logic)
        record = UserTable(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
        # Why merge? To avoid attaching detached instances.
        await self._session.merge(record) 
        # Note: commit() happens in the Service layer (Unit of Work), not here!

```

---

## 4. 🟡 The Application Service (The Brain)

**Location:** `src/app/services/`
**Rule:** Orchestration only. No SQL here. Dependency Injection via `__init__`.

```python
import structlog
from uuid import UUID
from src.domain.ports.user_repository import UserRepositoryProtocol
from src.domain.exceptions import UserNotFoundError

# Structured Logger (Crucial for Observability)
logger = structlog.get_logger()

class UserActivationService:
    def __init__(self, user_repo: UserRepositoryProtocol):
        self._repo = user_repo

    async def execute(self, user_id: UUID) -> None:
        """
        Orchestrates the activation use case.
        """
        # Contextual logging: Always bind IDs
        log = logger.bind(user_id=str(user_id))
        
        log.info("activation_started")

        user = await self._repo.get_by_id(user_id)
        if not user:
            log.error("activation_failed_user_not_found")
            raise UserNotFoundError(f"User {user_id} not found")

        # Domain Logic
        active_user = user.activate()

        # Persistence
        await self._repo.save(active_user)
        
        log.info("activation_completed", new_status=active_user.is_active)

```

---

## 5. 🟣 Dependency Injection (The Wiring)

**Location:** `src/entrypoints/api/dependencies.py`
**Rule:** Use `Annotated` and `Depends`. This builds the graph at runtime.

```python
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.db.session import get_db_session
from src.infra.db.repositories.user_repo import SqlAlchemyUserRepository
from src.domain.ports.user_repository import UserRepositoryProtocol
from src.app.services.activation_service import UserActivationService

# 1. Provide DB Session
async def get_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> UserRepositoryProtocol:
    return SqlAlchemyUserRepository(session)

# 2. Provide Service (Injecting Repository)
async def get_activation_service(
    repo: Annotated[UserRepositoryProtocol, Depends(get_repository)]
) -> UserActivationService:
    return UserActivationService(repo)

# 3. Use in Route
# @router.post("/activate")
# async def activate(
#     service: Annotated[UserActivationService, Depends(get_activation_service)]
# ): ...

```

---

## 6. 🧪 Testing (The Safety Net)

**Location:** `tests/unit/`
**Rule:** Mock the **Interface (Port)**, not the Database. Speed > Realism for unit tests.

```python
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from src.app.services.activation_service import UserActivationService
from src.domain.entities.user import UserProfile
from src.domain.ports.user_repository import UserRepositoryProtocol

@pytest.mark.asyncio
async def test_user_activation_success():
    # 1. Arrange
    mock_repo = Mock(spec=UserRepositoryProtocol)
    
    # Prepare data
    user_id = uuid4()
    inactive_user = UserProfile(id=user_id, email="test@space.com", is_active=False)
    
    # Mock return values (Simulate DB)
    mock_repo.get_by_id = AsyncMock(return_value=inactive_user)
    mock_repo.save = AsyncMock(return_value=None)

    service = UserActivationService(user_repo=mock_repo)

    # 2. Act
    await service.execute(user_id)

    # 3. Assert
    # Verify logic was called
    mock_repo.get_by_id.assert_called_once_with(user_id)
    
    # Verify save was called with ACTIVATED user
    saved_user = mock_repo.save.call_args[0][0]
    assert saved_user.is_active is True
    assert saved_user.id == user_id

```

---

## 7. ⚡ Structlog (The All-Seeing Eye)

**Location:** `src/logging.py`
**Rule:** Logs must be machine-readable (JSON in prod). Never use `print`. Request IDs are automatically bound by middleware.

```python
# BAD ❌
logger.info(f"User {user_id} failed to login") 
# Why bad? Unsearchable in Datadog/Splunk/Grafana.

# GOOD ✅
logger.info("login_failed", user_id=str(user_id), reason="invalid_password")
# Why good? Produces: {"event": "login_failed", "user_id": "...", "reason": "...", "request_id": "..."}
# Note: 'request_id' is automatically injected by CorrelationIdMiddleware.

```

---

## 8. 💎 Value Objects (Immutable Primitives)

**Location:** `src/domain/values.py`
**Rule:** Use `frozen=True`. Value Objects are defined by their attributes, not an ID. If you change a value, you get a NEW object.

```python
from pydantic import BaseModel, ConfigDict, field_validator

class Money(BaseModel):
    """
    Immutable Value Object.
    Prevents floating point errors in financial logic.
    """
    model_config = ConfigDict(frozen=True)  # 🔒 Immutable

    amount: int  # Stored in cents
    currency: str = "USD"

    @field_validator("amount")
    @classmethod
    def positive_only(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Negative money is debt, handle via Debt class.")
        return v

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(amount=self.amount + other.amount, currency=self.currency)

```

---

## 9. 🛡️ Error Hierarchy (Typed Failures)

**Location:** `src/domain/exceptions.py`
**Rule:** Never raise generic `Exception`. Create a hierarchy. This allows the API layer to map specific errors to HTTP 404/400/403 automatically.

```python
class DomainError(Exception):
    """Base class for all business logic errors."""
    pass

class ResourceNotFound(DomainError):
    """Maps to HTTP 404."""
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} with id {id} not found.")

class BusinessRuleViolation(DomainError):
    """Maps to HTTP 409 or 400."""
    pass

# Usage in Domain:
# raise ResourceNotFound("User", str(user_id))

```

---

## 10. ⚙️ Configuration (Strict Env)

**Location:** `src/settings.py`
**Rule:** Fail fast. If `OPENAI_API_KEY` is missing, the app should crash immediately at startup, not at runtime.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Infra
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    
    # Secrets (Hidden in logs automatically)
    OPENAI_API_KEY: SecretStr 
    
    # App Defaults
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

settings = Settings()
# Access: settings.OPENAI_API_KEY.get_secret_value()

```

---

## 11. 🤖 LangGraph Node (Functional Agent)

**Location:** `src/app/graph/nodes/interviewer.py`
**Rule:** Nodes are pure functions (or methods) that take `State` and return a `Dict` (Partial Update).

```python
from typing import Literal
from src.app.graph.state import AgentState  # TypedDict
from src.domain.ports.llm_provider import LLMProviderProtocol

async def interviewer_node(
    state: AgentState, 
    llm: LLMProviderProtocol
) -> dict[str, Any]:
    """
    Standard LangGraph Node.
    Returns specific keys to update in the global state.
    """
    messages = state["history"]
    profile = state["profile"]
        
    # 1. Logic (Call LLM)
    response = await llm.generate(
        system_prompt="You are a recruiter...",
        messages=messages,
        context=profile
    )

    # 2. Return State Update (Merged automatically by LangGraph)
    return {
        "history": [response],     # Appends to list
        "step_count": state["step_count"] + 1,
        "last_agent": "interviewer"
    }

```

---

## 12. 🧱 API DTOs ( The Firewall)

**Location:** `src/entrypoints/api/schemas.py`
**Rule:** NEVER return Domain Entities directly from API. Leakage of internal structure prevents refactoring.

```python
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

# 🟢 REQUEST (Input)
class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    # Note: No 'is_active' or 'id' here. User cannot set them.

# 🔵 RESPONSE (Output)
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    # Flattened data for frontend convenience
    joined_at: datetime 
    
    @classmethod
    def from_domain(cls, entity: "UserProfile") -> "UserResponse":
        """Explicit mapper method."""
        return cls(
            id=entity.id,
            email=entity.email,
            is_active=entity.is_active,
            joined_at=entity.created_at
        )

```

---

## 13. 🔁 Resilience (The Retry Decorator)

**Location:** `src/infra/llm/client.py`
**Rule:** Network calls fail. LLMs timeout. Retries must be exponential, distinct from business logic.

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class OpenAIClient:
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.ConnectTimeout),
        reraise=True
    )
    async def generate(self, prompt: str) -> str:
        """
        Retries 3 times with 2s, 4s, 8s backoff.
        Only retries on network errors, NOT on 400 Bad Request.
        """
        # ... implementation ...
        pass

```

---

## 14. 🛡️ Security (The Guardrails)

**Location:** `src/infra/security/sanitization.py`
**Rule:** Trust No One. All external inputs (API payloads, Webhook data) must be sanitized *at the boundary* before reaching business logic or the graph.

```python
from src.infra.security.sanitization import sanitize_input
from pydantic import field_validator

class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        # 1. HTML Escape (<script> -> &lt;script&gt;)
        # 2. Strip whitespace
        return sanitize_input(v)
```
