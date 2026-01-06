from typing import Any

from fastapi import Request


def get_graph(request: Request) -> Any:
    """
    Retrieves the initialized LangGraph runnable from the app state.
    """
    if not hasattr(request.app.state, "graph"):
        raise RuntimeError("Graph has not been initialized in app state.")
    return request.app.state.graph
