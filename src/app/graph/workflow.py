from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.app.graph.nodes.architect import architect_node
from src.app.graph.nodes.critic import critic_node
from src.app.graph.nodes.interviewer import interviewer_node
from src.app.graph.state import AgentState


def should_continue(state: AgentState) -> str:
    """
    Decides the next step after the Critic.
    """
    critique = state.get("critique")
    
    if critique and critique.is_approved:
        return "interviewer"
    
    if state.get("step_count", 0) > 5:
        return "interviewer"
        
    return "architect"

def create_graph(checkpointer: Any = None) -> Any:
    """
    Constructs the Agentic Workflow Graph.
    """
    workflow = StateGraph(AgentState)

    workflow = StateGraph(AgentState)

    workflow.add_node("architect", architect_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("interviewer", interviewer_node)

    workflow.add_edge(START, "architect")
    workflow.add_edge("architect", "critic")
    
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "interviewer": "interviewer",
            "architect": "architect"
        }
    )
    
    workflow.add_edge("interviewer", END)

    checkpointer = checkpointer or MemorySaver()

    # 4. Compile
    return workflow.compile(checkpointer=checkpointer)


graph_runnable = create_graph()
