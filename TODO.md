# 📋 TODO: Improvements & Future Enhancements

> **Status**: Last Updated 2026-01-11
> **Priority Levels**: 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## 🟡 Medium Priority

### 1. Performance - Database Connection Pooling
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

## 🔮 Backlog / Future Improvements

### Prompt Engineering
- [ ] Implement prompt versioning strategy (e.g., `architect_v2.j2`)
- [ ] Consider implementing prompt registry for A/B testing

### Telegram Integration
- [ ] Handle Markdown → HTML conversion for responses

### Observability & Logging
- [ ] Add sampling for high-volume logs

### Rate Limiting & Throttling
- [ ] Add per-user quotas
- [ ] Add circuit breaker for LLM budget exceeded
- [ ] Create admin dashboard for usage monitoring

### Security & Validation
- [ ] Implement profanity filter
- [ ] Add XSS/injection prevention for user inputs

---

## 📊 Summary Statistics

- **Active Items**: 1 (Performance)
- **Backlog Items**: 8
- **Completed**: Previous milestones archived.
