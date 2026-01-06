from src.app.prompts.renderer import render_prompt


def test_render_prompt_architect():
    rendered = render_prompt(
        "architect.j2", 
        user_profile_json='{"name": "test"}', 
        user_request="test request"
    )
    assert "Architect" in rendered
    assert "test request" in rendered

def test_render_prompt_critic():
    rendered = render_prompt("critic.j2", plan_json='{}')
    assert "Critic" in rendered

def test_render_prompt_interviewer():
    rendered = render_prompt("interviewer.j2", context="test context")
    assert "Interviewer" in rendered
    assert "test context" in rendered
