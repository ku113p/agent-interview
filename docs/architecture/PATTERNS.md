# Patterns

Each pattern below is a precise reminder for agents and humans about how the code must behave. Keep these summaries short, factual, and actionable.

---

## 1. Domain Layer
- Location: `src/domain/*` (entities, ports, events).
- Rule: Zero imports from infra, app, or entrypoints. Models must be pure Pydantic V2.
- Agents: Trust these models for validation and business invariants.

---

## 2. Ports (Protocols)
- Define contracts (e.g., `UserRepositoryProtocol`) and nothing else.
- Infra implements the protocols; graph logic depends on them.

---

## 3. LangGraph Nodes (The Agent Pattern)
- **Location**: `src/app/graph/nodes/*.py`
- **Signature**: `async def node_name(state: AgentState, config: RunnableConfig) -> dict[str, Any]`
- **Rule**:
    1.  **Stateless**: Nodes rely on `state` and `config`.
    2.  **Service Injection**: Get services from `config["configurable"]`.
    3.  **Partial Update**: Return a `dict` to patch the state.
    4.  **Observation**: Decorate with `@observe()`.

```python
@observe()
async def architect_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    # 1. Inject Dependencies
    configurable = config.get("configurable", {})
    db_session = configurable.get("db_session")

    # 2. Logic
    # ...

    # 3. Return Patch
    return {"step_count": state["step_count"] + 1}
```

---

## 4. Prompts (Jinja2)
- **Location**: `src/app/prompts/*.j2`
- **Rule**: Separation of prompt text and logic.
- **Components**:
    -   `registry.py`: Maps names to files.
    -   `renderer.py`: Renders template with context.
    -   Usage: `render_prompt("architect", user_id=uid, ...)`

---

## 5. Testing
- **Unit**: `tests/unit/`. Mock protocols.
- **Async**: Use `@pytest.mark.asyncio`.

---

## 6. Adapter Implementation (Infra)
- **Location**: `src/infra/db/repositories/`
- **Rule**: Map SQL Models <-> Domain Entities explicitly. Use `AsyncSession`.

---

## 7. Configuration
- **Location**: `src/settings.py`
- **Rule**: Fail fast at startup if env vars are missing. Use `pydantic-settings`.
