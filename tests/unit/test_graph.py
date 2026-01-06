import pytest
from src.app.graph.workflow import create_graph

@pytest.mark.asyncio
async def test_graph_initialization():
    app = create_graph()
    assert app is not None
    
@pytest.mark.asyncio
async def test_graph_execution_flow():
    app = create_graph()
    
    # Initial State
    initial_state = {
        "messages": [{"role": "user", "content": "Hi there"}],
        "user_id": "test_user",
        "step_count": 0,
        "error_count": 0,
        "last_agent": "start",
        "plan": None
    }
    
    # Run the graph
    # config is required for checkpointer
    config = {"configurable": {"thread_id": "test_thread"}}
    
    final_state = await app.ainvoke(initial_state, config=config)
    
    # Verify the flow: update step count, last agent
    assert final_state["step_count"] > 0
    assert final_state["last_agent"] == "interviewer"
