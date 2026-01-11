from src.entrypoints.telegram.formatting import markdown_to_telegram_html


def test_basic_formatting():
    markdown = "**Bold** and *Italic*"
    expected = "<b>Bold</b> and <i>Italic</i>"
    assert markdown_to_telegram_html(markdown).strip() == expected


def test_headers_to_bold():
    markdown = "# Header 1\n## Header 2"
    # Headers become bold lines
    expected = "<b>Header 1</b>\n\n<b>Header 2</b>"
    assert markdown_to_telegram_html(markdown).strip() == expected


def test_lists_unordered():
    markdown = "* Item 1\n* Item 2"
    # Lists become bullet points
    expected = "• Item 1\n• Item 2"
    assert markdown_to_telegram_html(markdown).strip() == expected


def test_lists_ordered():
    markdown = "1. First\n2. Second"
    # Ordered lists also become bullet points (simplification) or numbered if supported
    # For now, our parser will treat li as bullet points for simplicity,
    # or we can try to preserve numbers. Let's assume bullets for now as it's safer.
    expected = "• First\n• Second"
    assert markdown_to_telegram_html(markdown).strip() == expected


def test_code_blocks():
    markdown = "```python\nprint('hello')\n```"
    # Fenced code should be pre code
    # Note: markdown lib might add class="language-python"
    # The parser uses quote=False for escaping, so ' remains '
    # Markdown adds a newline at the end of code block content
    expected = "<pre><code class=\"language-python\">print('hello')\n</code></pre>"
    assert markdown_to_telegram_html(markdown).strip() == expected


def test_html_entity_escaping():
    markdown = "x < y & z > a"
    # Entities must be escaped in the output HTML
    expected = "x &lt; y &amp; z &gt; a"
    assert markdown_to_telegram_html(markdown).strip() == expected


def test_inline_code():
    markdown = "`code`"
    expected = "<code>code</code>"
    assert markdown_to_telegram_html(markdown).strip() == expected


def test_links():
    markdown = "[Google](https://google.com)"
    expected = '<a href="https://google.com">Google</a>'
    assert markdown_to_telegram_html(markdown).strip() == expected


def test_paragraph_handling():
    markdown = "Line 1\n\nLine 2"
    # Paragraphs should be separated by double newlines
    expected = "Line 1\n\nLine 2"
    assert markdown_to_telegram_html(markdown).strip() == expected
