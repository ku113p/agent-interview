from src.app.prompts.renderer import render_prompt


def test_render_prompt_architect():
    rendered = render_prompt(
        "architect_v1.j2",
        user_profile_json='{"name": "test"}',
        user_request="test request",
    )
    assert "Architect" in rendered
    assert "test request" in rendered


def test_render_prompt_architect_logical_key():
    rendered = render_prompt(
        "architect",
        user_profile_json='{"name": "test"}',
        user_request="test request",
    )
    assert "Architect" in rendered
    assert "test request" in rendered


def test_render_prompt_critic():
    rendered = render_prompt("critic_v1.j2", plan_json="{}")
    assert "Critic" in rendered


def test_render_prompt_interviewer():
    rendered = render_prompt("interviewer_v1.j2", context="test context")
    assert "Interviewer" in rendered
    assert "test context" in rendered
