import json
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def jinja_env() -> Environment:
    """Create Jinja2 environment for prompt templates."""
    templates_dir = (
        Path(__file__).parent.parent.parent.parent.parent / "src" / "app" / "prompts"
    )
    return Environment(loader=FileSystemLoader(str(templates_dir)))


def test_architect_template_renders_with_valid_data(jinja_env: Environment) -> None:
    """Test that architect template renders correctly with valid data."""
    template = jinja_env.get_template("architect.j2")

    user_profile = {"name": "John Doe", "profession": "Software Engineer"}
    rendered = template.render(
        user_profile_json=json.dumps(user_profile),
        user_request="Help me prepare for interviews",
    )

    assert "Architect" in rendered
    assert "John Doe" in rendered
    assert "Help me prepare for interviews" in rendered


def test_architect_template_handles_empty_profile(jinja_env: Environment) -> None:
    """Test that architect template handles empty profile gracefully."""
    template = jinja_env.get_template("architect.j2")

    rendered = template.render(user_profile_json="{}", user_request="Test request")

    assert "Architect" in rendered
    assert "Test request" in rendered


def test_architect_template_renders_special_characters(jinja_env: Environment) -> None:
    """Test that template handles special characters in user input."""
    template = jinja_env.get_template("architect.j2")

    user_profile = {"name": "User's Name", "skills": "Python & JavaScript"}
    rendered = template.render(
        user_profile_json=json.dumps(user_profile),
        user_request="Review my resume (2024 version)",
    )

    assert "User's Name" in rendered
    assert "Python & JavaScript" in rendered or "Python &amp; JavaScript" in rendered
    assert "2024" in rendered


def test_critic_template_renders(jinja_env: Environment) -> None:
    """Test that critic template renders correctly."""
    template = jinja_env.get_template("critic.j2")
    rendered = template.render(plan_json='{"steps": ["A"]}')
    assert "Critic" in rendered
    assert '"steps": ["A"]' in rendered


def test_interviewer_template_renders(jinja_env: Environment) -> None:
    """Test that interviewer template renders correctly."""
    template = jinja_env.get_template("interviewer.j2")
    rendered = template.render(context="Some context")
    assert "Interviewer" in rendered
    assert "Some context" in rendered
