from src.infra.security.sanitization import sanitize_input


def test_sanitize_clean_string() -> None:
    """Verify normal text is unchanged."""
    assert sanitize_input("Hello World") == "Hello World"


def test_sanitize_xss_payload() -> None:
    """Verify <script> tags are escaped."""
    payload = "<script>alert(1)</script>"
    expected = "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert sanitize_input(payload) == expected


def test_sanitize_special_chars() -> None:
    """Verify quotes and ampersands are escaped."""
    payload = 'User "Test" & Co'
    expected = "User &quot;Test&quot; &amp; Co"
    assert sanitize_input(payload) == expected


def test_sanitize_whitespace() -> None:
    """Verify trimming."""
    assert sanitize_input("  hello  ") == "hello"


def test_sanitize_empty() -> None:
    """Verify empty string returns empty string."""
    assert sanitize_input("") == ""
