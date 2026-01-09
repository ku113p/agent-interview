# 📋 TODO: Improvements & Future Enhancements

> **Status**: Last Updated 2026-01-06 23:25  
> **Priority Levels**: 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low  
> **Completed This Session**: 2 Critical items ✅

---

## 🔴 Critical Priority

### 1. Domain Layer - Exception Hierarchy Missing
**Status**: ✅ **COMPLETED** (2026-01-06)  
**Impact**: High - All error handling uses generic exceptions  
**Description**: The [PATTERNS.md](docs/architecture/PATTERNS.md) and [ARCHITECTURE_DECISIONS.md](docs/architecture/DECISIONS.md) reference a Domain Exception hierarchy, but it doesn't exist in the codebase.

**Action Items**:
- [x] Create `src/domain/exceptions.py` with:
  - `DomainError` (base class)
  - `ResourceNotFound` (maps to HTTP 404)
  - `BusinessRuleViolation` (maps to HTTP 400/409)
  - `UserNotFoundError`, `MemoryNotFoundError`, etc.
  - `LLMError`, `LLMTimeoutError`, `LLMResponseError` (bonus)
- [x] Update all domain entities to raise typed exceptions
- [x] Create FastAPI exception handlers to map domain errors to HTTP responses
- [x] Update tests to verify exception behavior

**Files Created**:
- ✅ `src/domain/exceptions.py` 
- ✅ `src/entrypoints/api/error_handlers.py`
- ✅ `tests/unit/domain/test_exceptions.py`
- ✅ Updated `src/main.py` to register error handlers
- ✅ Updated `src/infra/llm/client.py` to use LLM exceptions

---

### 2. Prompt Engineering - Prompts Are Hardcoded
**Status**: ✅ **COMPLETED** (2026-01-06)  
**Impact**: High - Cannot A/B test or version prompts  
**Description**: All prompts are now externalized to Jinja2 templates.

**Action Items**:
- [x] Create Jinja2 templates for all agent nodes:
  - `src/app/prompts/critic.j2`
  - `src/app/prompts/interviewer.j2`
- [x] Create prompt rendering service/utility
- [x] Add prompt validation tests
- [ ] Implement prompt versioning strategy (e.g., `architect_v2.j2`) - **FUTURE**
- [ ] Consider implementing prompt registry for A/B testing - **FUTURE**

**Files Created**:
- ✅ `src/app/prompts/critic.j2`
- ✅ `src/app/prompts/interviewer.j2`
- ✅ `src/app/prompts/renderer.py`
- ✅ `tests/unit/app/prompts/test_renderer.py`
- ✅ Updated `src/app/graph/nodes/architect.py`
- ✅ Updated `src/app/graph/nodes/critic.py`
- ✅ Updated `src/app/graph/nodes/interviewer.py`

**Benefits Achieved**:
- Zero hardcoded prompts in Python code
- Can swap prompt versions without code changes
- Ready for A/B testing when needed

---

### 3. Telegram Integration - Core Implementation Complete
**Status**: ✅ **COMPLETED** (2026-01-06)
**Impact**: High - Cannot use Telegram bot  
**Description**: Webhook endpoint exists but doesn't process messages or integrate with the graph.

**Action Items**:
- [x] Implement actual message processing in webhook
- [x] Add Telegram Bot API client wrapper
- [x] Forward messages to agent graph
- [ ] Handle Markdown → HTML conversion for responses
- [x] Implement proper error handling and retry logic
- [x] Add user session management (map Telegram user_id to thread_id)
- [x] Create Telegram-specific configuration in settings

**Files to Create/Modify**:
- ✅ `src/entrypoints/telegram/webhook.py` (complete implementation)
- ✅ `src/entrypoints/telegram/client.py` (new - Telegram API wrapper)
- ✅ `src/settings.py` (add TELEGRAM_BOT_TOKEN)

---

## 🟠 High Priority

### 4. Database Session Management - Missing in Graph Nodes
**Status**: ✅ **COMPLETED** (2026-01-07)
**Impact**: High - Graph nodes cannot access database  
**Description**: Graph nodes need to save/retrieve user profiles and memories, but there's no dependency injection for DB sessions.

**Action Items**:
- [x] Implement partial config pattern for node injection
- [x] Create `get_db_session` dependency
- [x] Create `get_memory_service` dependency
- [x] Modify graph nodes to accept dependencies
- [x] Update workflow to compile with RunnableConfig bindings
- [x] Add integration tests for DB access in nodes (Unit tests added for injection)

**Files to Create/Modify**:
- `src/app/dependencies.py` (expand with DB/Memory dependencies)
- `src/app/graph/workflow.py` (add dependency binding)
- `src/app/graph/nodes/*.py` (update signatures)

---

### 5. Memory Integration - Partially Implemented
**Status**: ⚠️ Partial
**Impact**: High - Agents require memory to be effective.
**Description**: `mem0ai` has been integrated as the primary memory service, replacing the previous `RedisMemoryService`. The Architect node now retrieves memories to inform planning.

**Action Items**:
- [x] Integrate `mem0ai` library and configure for local Qdrant storage.
- [x] Implement memory retrieval in Architect node.
- [x] Add context injection to prompts based on retrieved memories (for Architect).
- [ ] Implement memory storage in Interviewer node.
- [ ] Create memory extraction logic from conversations (Handled by `mem0ai`).
- [ ] Implement importance scoring algorithm (Handled by `mem0ai`).
- [ ] Add memory pruning/consolidation strategy (Handled by `mem0ai`).

**Files to Create/Modify**:
- `src/infra/mem0/client.py` (new)
- `src/app/graph/nodes/architect.py` (add memory retrieval)
- `src/app/graph/nodes/interviewer.py` (add memory storage)
- `src/app/services/memory_extractor.py` (new)

---

### 6. Observability - LangFuse Not Integrated
**Status**: ❌ Not Implemented  
**Impact**: Medium-High - Cannot debug agent behavior  
**Description**: [ARCHITECTURE_DECISIONS.md](docs/architecture/DECISIONS.md) mandates LangFuse integration with `@observe` decorators, but none present.

**Action Items**:
- [ ] Install `langfuse` SDK
- [ ] Configure LangFuse connection in settings
- [ ] Add `@observe` decorators to:
  - Graph entry points
  - LLM client methods
  - Key service methods
- [ ] Add custom spans for graph node transitions
- [ ] Create dashboard config for key metrics
- [ ] Document LangFuse setup in README

**Files to Create/Modify**:
- `pyproject.toml` (add langfuse dependency)
- `src/settings.py` (add LANGFUSE_* config)
- `src/infra/llm/client.py` (add @observe)
- `src/app/graph/workflow.py` (add tracing)

---

### 7. User Data Layer (Profiles & Spheres)
**Status**: ⚠️ Partial
**Impact**: High - Core of V2 architecture for organizing data collection.
**Description**: `UserProfile` and `Sphere` entities and repositories are implemented, but not fully integrated into the agent workflow.

**Action Items**:
- [x] Implement `Sphere` domain entity and SQLAlchemy repository.
- [x] Add Sphere repository to dependency injection.
- [x] Update Architect node to be aware of Spheres.
- [ ] Create user profile lookup/creation in chat endpoint.
- [ ] Inject user profile into AgentState.
- [ ] Use profile data in Architect node planning.
- [ ] Update profile based on conversation (profession, experience_years).
- [ ] Add profile and sphere management endpoints (GET/POST/PATCH for users and spheres).

**Files to Create/Modify**:
- `src/domain/entities/sphere.py` (created)
- `src/domain/ports/sphere_repository.py` (created)
- `src/infra/db/models.py` (updated with SphereTable)
- `src/infra/db/repositories/sphere_repo.py` (created)
- `src/entrypoints/api/router.py` (add profile lookup)
- `src/app/graph/state.py` (add user_profile and current_sphere_id fields)
- `src/entrypoints/api/users.py` (new - user CRUD endpoints)
- `src/entrypoints/api/spheres.py` (new - sphere CRUD endpoints)

---

## 🟡 Medium Priority

### 8. Configuration Management - Too Many Defaults
**Status**: ⚠️ Acceptable but Risky  
**Impact**: Medium - Can start with invalid config  
**Description**: Settings have too many defaults (API key, DB URL). Should fail fast on missing critical values.

**Action Items**:
- [ ] Remove defaults for critical settings (OPENAI_API_KEY, DATABASE_URL)
- [ ] Add environment-specific configs (local.env, prod.env)
- [ ] Implement config validation on startup
- [ ] Add health check endpoint that verifies DB/Redis connectivity
- [ ] Document all required environment variables

**Files to Create/Modify**:
- `src/settings.py` (remove Field defaults)
- `src/entrypoints/api/health.py` (new - health checks)
- `.env.example` (new)

---

### 9. API DTOs - Direct State Exposure
**Status**: ⚠️ Acceptable but Not Best Practice  
**Impact**: Medium - Breaks encapsulation  
**Description**: [PATTERNS.md](docs/architecture/PATTERNS.md) warns against exposing internal state directly. Current API returns raw state snapshot.

**Action Items**:
- [ ] Create proper DTOs for API responses
- [ ] Implement `ChatResponse.from_state()` mapper
- [ ] Create `ThreadStateResponse` for debug endpoint
- [ ] Hide internal fields (error_count, retry_depth)
- [ ] Version API responses (v1 prefix)

**Files to Create/Modify**:
- `src/entrypoints/api/schemas.py` (new)
- `src/entrypoints/api/router.py` (use DTOs)

---

### 10. Graph State - Missing Conversation History Management
**Status**: ⚠️ Messages accumulate indefinitely  
**Impact**: Medium - Will hit token limits  
**Description**: No logic to prune old messages or summarize conversation history.

**Action Items**:
- [ ] Implement message window strategy (keep last N messages)
- [ ] Add conversation summarization node
- [ ] Implement sliding window context management
- [ ] Add token counting to prevent context overflow
- [ ] Store full history in DB, use summarized version in state

**Files to Create/Modify**:
- `src/app/graph/state.py` (add context management)
- `src/app/graph/nodes/summarizer.py` (new)
- `src/app/services/context_manager.py` (new)

---

### 11. Testing - Integration Tests Missing
**Status**: ❌ Not Implemented  
**Impact**: Medium - Can't verify infra layer properly  
**Description**: [TESTING.md](docs/guides/TESTING.md) mentions integration tests but none exist.

**Action Items**:
- [ ] Create `tests/integration/` directory
- [ ] Add DB integration tests with real Postgres
- [ ] Add Redis integration tests
- [ ] Add API integration tests (full request/response)
- [ ] Use pytest fixtures for DB setup/teardown
- [ ] Implement test containers or docker-compose test profile

**Files to Create/Modify**:
- `tests/integration/test_db_repositories.py` (new)
- `tests/integration/test_redis_memory.py` (new)
- `tests/integration/test_api_full_flow.py` (new)

---

### 12. Async LLM Client - Message Conversion Fragile
**Status**: ⚠️ Works but Not Robust  
**Impact**: Medium - May fail with unexpected message formats  
**Description**: `_convert_messages` method has many fallbacks and type coercion.

**Action Items**:
- [ ] Define strict Message protocol/interface
- [ ] Add input validation with Pydantic
- [ ] Remove "best guess" fallbacks
- [ ] Add specific error messages for unsupported formats
- [ ] Create tests for all message format variations

**Files to Create/Modify**:
- `src/infra/llm/messages.py` (new - message types)
- `src/infra/llm/client.py` (use strict types)

---

## 🟢 Low Priority (Nice to Have)

### 13. Workflow Duplication
**Status**: ⚠️ Minor Code Smell  
**Impact**: Low - Works fine  
**Description**: In `workflow.py` line 33, `workflow = StateGraph(AgentState)` is defined twice.

**Action Items**:
- [ ] Remove duplicate line 33

**Files to Modify**:
- `src/app/graph/workflow.py`

---

### 14. Logging Enhancement
**Status**: ⚠️ Basic Logging Implemented  
**Impact**: Low - Current logging is functional  
**Description**: Could benefit from more structured logging with correlation IDs.

**Action Items**:
- [ ] Add request correlation IDs
- [ ] Implement context-bound logging
- [ ] Add performance metrics logging
- [ ] Create log aggregation configuration
- [ ] Add sampling for high-volume logs

**Files to Modify**:
- `src/logging.py` (new)
- `src/main.py` (add middleware)

---

### 15. Development Experience - Hot Reload for Prompts
**Status**: ❌ Not Implemented  
**Impact**: Low - Manual restart works  
**Description**: Changing prompts requires server restart.

**Action Items**:
- [ ] Implement prompt file watcher
- [ ] Add hot reload for Jinja templates
- [ ] Create prompt management CLI tool
- [ ] Add prompt version comparison tool

**Files to Create/Modify**:
- `src/app/prompts/watcher.py` (new)

---

### 16. Rate Limiting & Throttling
**Status**: ❌ Not Implemented  
**Impact**: Low - OK for MVP  
**Description**: No protection against abuse or cost overruns.

**Action Items**:
- [ ] Implement rate limiting middleware
- [ ] Add per-user quotas
- [ ] Create cost tracking per user/thread
- [ ] Add circuit breaker for LLM budget exceeded
- [ ] Create admin dashboard for usage monitoring

**Files to Create/Modify**:
- `src/middleware/rate_limiter.py` (new)
- `src/services/cost_tracker.py` (new)

---

### 17. Data Validation - Message Content
**Status**: ⚠️ Basic Validation  
**Impact**: Low  
**Description**: No maximum length or content validation on user messages.

**Action Items**:
- [ ] Add max message length validation
- [ ] Implement profanity filter (if needed)
- [ ] Add XSS/injection prevention
- [ ] Validate thread_id format

**Files to Modify**:
- `src/entrypoints/api/router.py` (add validators)

---

### 18. Documentation - API Documentation
**Status**: ⚠️ Basic (FastAPI auto-docs only)  
**Impact**: Low  
**Description**: No detailed API usage guide.

**Action Items**:
- [ ] Create `docs/API.md` with examples
- [ ] Add request/response examples
- [ ] Document authentication (when added)
- [ ] Create Postman/Insomnia collection
- [ ] Add sequence diagrams for flows

**Files to Create/Modify**:
- `docs/API.md` (new)
- `docs/ARCHITECTURE.md` (new - detailed diagrams)

---

### 19. Performance - Database Connection Pooling
**Status**: ⚠️ Using defaults  
**Impact**: Low - OK for current scale  
**Description**: No explicit connection pool configuration.

**Action Items**:
- [ ] Configure SQLAlchemy pool size
- [ ] Add connection pool monitoring
- [ ] Tune pool parameters for production
- [ ] Add connection leak detection

**Files to Modify**:
- `src/infra/db/session.py`

---

### 20. Security - Secrets Management
**Status**: ⚠️ Using .env  
**Impact**: Low - OK for development  
**Description**: Secrets in .env file, not production-ready.

**Action Items**:
- [ ] Integrate with secrets manager (AWS Secrets, Vault)
- [ ] Implement secret rotation
- [ ] Add audit logging for secret access
- [ ] Use environment-specific secret backends

**Files to Modify**:
- `src/settings.py` (add secrets backend support)

---

## 📊 Summary Statistics

- **Total Items**: 20
- **Completed (\u2705)**: 2 (10%)
- **Partial (\u26a0\ufe0f)**: 2 (Memory Integration, User Data Layer)
- **Critical (\ud83d\udd34)**: 1 remaining (2 completed)
- **High (\ud83d\udfe0)**: 4 (1 partial)
- **Medium (\ud83d\udfe1)**: 5
- **Low (\ud83d\udfe2)**: 7

**Estimated Implementation Time** (Remaining):
- Critical: ~7 days (Telegram Integration)
- High: ~1 week
- Medium: ~3-4 days
- Low: ~1-2 days

**Total Remaining**: ~2.5-3 weeks for complete implementation

**Progress**: 2/20 items completed, 2 partial (20% effective progress) - \ud83c\udf89 Great start!
