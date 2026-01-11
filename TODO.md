# 📋 TODO: Improvements & Future Enhancements

> **Status**: Last Updated 2026-01-11
> **Priority Levels**: 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## 🟡 Medium Priority

### 1. Performance - Database Connection Pooling
**Status**: 🟢 Completed
**Impact**: Low - OK for current scale  
**Description**: Configured connection pool and monitoring.

**Action Items**:
- [x] Configure SQLAlchemy pool size
- [x] Add connection pool monitoring
- [x] Tune pool parameters for production
- [x] Add connection leak detection

**Files to Modify**:
- `src/infra/db/session.py`

---

## 🔮 Backlog / Future Improvements

### Prompt Engineering
- [x] Implement prompt versioning strategy (e.g., `architect_v2.j2`)
- [x] Consider implementing prompt registry for A/B testing

### Telegram Integration
- [x] Handle Markdown → HTML conversion for responses


### Observability & Logging
- [ ] Add sampling for high-volume logs

### Rate Limiting & Throttling
- [ ] Add per-user quotas
- [ ] Add circuit breaker for LLM budget exceeded
- [ ] Create admin dashboard for usage monitoring

### Security & Validation
- [x] Implement profanity filter
- [x] Add XSS/injection prevention for user inputs

---

## 📊 Summary Statistics

- **Active Items**: 1 (Performance)
- **Backlog Items**: 8
- **Completed**: Previous milestones archived.
