from src.app.graph.workflow import should_continue
from src.app.schemas import CritiqueSchema


def test_should_continue_to_interviewer_if_approved() -> None:
    state = {
        "critique": CritiqueSchema(is_approved=True, feedback="Good", score=10),
        "step_count": 1,
    }
    assert should_continue(state) == "interviewer"


def test_should_continue_to_architect_if_rejected() -> None:
    state = {
        "critique": CritiqueSchema(is_approved=False, feedback="Bad", score=2),
        "step_count": 1,
    }
    assert should_continue(state) == "architect"


def test_should_abort_to_interviewer_if_too_many_steps() -> None:
    state = {
        "critique": CritiqueSchema(is_approved=False, feedback="Bad", score=2),
        "step_count": 6,
    }
    assert should_continue(state) == "interviewer"


def test_should_loop_if_no_critique_yet() -> None:
    state = {"critique": None, "step_count": 1}
    assert should_continue(state) == "architect"
