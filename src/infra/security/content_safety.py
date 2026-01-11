from typing import Final

# A basic list of blocked terms for demonstration purposes.
# In a real production environment, this should be more comprehensive
# or use an external service.
BLOCKED_TERMS: Final[set[str]] = {
    "badword",
    "offensive",
    "profanity",
    # Add other terms as needed
}


def contains_profanity(text: str) -> bool:
    """
    Check if the text contains any blocked profanity terms.
    The check is case-insensitive.
    """
    if not text:
        return False

    normalized_text = text.lower()

    # Simple keyword matching
    # Note: This is a basic implementation. A more robust solution might use
    # regex for word boundaries or a dedicated library.
    for term in BLOCKED_TERMS:
        if term in normalized_text:
            return True

    return False
