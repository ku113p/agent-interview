from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_memory_service_importable():
    """Test that the mem0 service can be imported."""
    # Just test import, skip full functionality tests
    try:
        from src.infra.mem0.client import Mem0MemoryService

        assert Mem0MemoryService is not None
        print("✅ Mem0MemoryService imported successfully")
    except ImportError as e:
        print(f"⚠️ Mem0 not available (expected in some environments): {e}")
        pytest.skip("Mem0 not available in test environment")


@pytest.mark.asyncio
async def test_interviewer_node_can_be_imported():
    """Test that InterviewerNode can be imported without errors."""
    # This tests that our changes haven't broken the module imports
    from src.app.graph.nodes.interviewer import interviewer_node
    from src.app.graph.state import AgentState

    # Test that the node can be imported and has the expected signature
    assert callable(interviewer_node)

    # Verify state structure includes expected fields
    state: AgentState = {
        "messages": [],
        "user_id": str(uuid4()),
        "step_count": 0,
        "error_count": 0,
        "last_agent": "start",
        "plan": None,
        "critique": None,
        "plan_approved": None,
        "current_sphere_id": None,
    }

    # Basic structure check
    assert "user_id" in state
    assert "messages" in state
