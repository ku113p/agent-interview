from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.settings import settings


class PromptRenderer:
    def __init__(self, templates_dir: str | Path | None = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent

        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(),
            auto_reload=(settings.ENVIRONMENT == "local"),
        )

    def render(self, template_name: str, **kwargs: Any) -> str:
        template = self.env.get_template(template_name)
        return template.render(**kwargs)


# Singleton for easy access
renderer = PromptRenderer()


def render_prompt(template_name: str, **kwargs: Any) -> str:
    return renderer.render(template_name, **kwargs)
