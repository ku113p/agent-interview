from src.infra.security.content_safety import contains_profanity


def test_contains_profanity_clean() -> None:
    assert contains_profanity("Hello world") is False
    assert contains_profanity("This is a safe message") is False


def test_contains_profanity_dirty() -> None:
    assert contains_profanity("This message contains badword") is True
    assert contains_profanity("Using offensive language") is True


def test_contains_profanity_case_insensitive() -> None:
    assert contains_profanity("BaDwOrD") is True
    assert contains_profanity("OFFENSIVE") is True


def test_contains_profanity_empty() -> None:
    assert contains_profanity("") is False
    assert contains_profanity(None) is False  # type: ignore
