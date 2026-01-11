import html


def sanitize_input(value: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.

    - Escapes HTML special characters (<, >, &, ", ').
    - Strips leading/trailing whitespace.
    """
    if not value:
        return ""
    return html.escape(value).strip()
