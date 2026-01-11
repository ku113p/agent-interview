import html
from html.parser import HTMLParser

import markdown


class TelegramHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.output: list[str] = []
        self.tag_stack: list[str] = []

        # Mapping standard tags to Telegram supported tags
        self.tag_map = {
            "strong": "b",
            "b": "b",
            "em": "i",
            "i": "i",
            "code": "code",
            "pre": "pre",
            "a": "a",
            "u": "u",
            "s": "s",
            "del": "s",
            "strike": "s",
        }

        # Tags that we strip but keep content
        self.ignored_tags = {"p", "div", "span", "html", "body", "ul", "ol"}

        # Tags that we convert to bold
        self.header_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.tag_map:
            tg_tag = self.tag_map[tag]
            attrs_str = ""
            if tag == "a":
                href = dict(attrs).get("href")
                if href:
                    attrs_str = f' href="{html.escape(href)}"'
            elif tag == "code":
                cls = dict(attrs).get("class")
                if cls:
                    attrs_str = f' class="{html.escape(cls)}"'

            self.output.append(f"<{tg_tag}{attrs_str}>")
            self.tag_stack.append(tg_tag)

        elif tag in self.header_tags:
            self.output.append("<b>")
            self.tag_stack.append("b")

        elif tag == "li":
            self.output.append("• ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.tag_map:
            tg_tag = self.tag_map[tag]
            if self.tag_stack and self.tag_stack[-1] == tg_tag:
                self.output.append(f"</{tg_tag}>")
                self.tag_stack.pop()

        elif tag in self.header_tags:
            self.output.append("</b>\n\n")
            if self.tag_stack and self.tag_stack[-1] == "b":
                self.tag_stack.pop()

        elif tag == "p":
            self.output.append("\n\n")

        elif tag == "li":
            self.output.append("\n")

    def handle_data(self, data: str) -> None:
        # Ignore whitespace-only data between block tags (root level or inside lists)
        # We assume block tags are p, h1-h6, li, ul, ol, div
        # If we are inside b, i, a, code, pre, we keep everything

        # Check if we are inside an "inline" context where whitespace matters
        inline_tags = {"b", "i", "a", "code", "pre", "strong", "em", "span"}
        is_inline = False
        for tag in self.tag_stack:
            if tag in inline_tags:
                is_inline = True
                break

        if not is_inline and not data.strip():
            # We are between blocks, likely formatting newlines from markdown output
            return

        # Crucial: Escape data to prevent broken HTML
        # quote=False: Telegram text content doesn't need quotes escaped, only < > &
        self.output.append(html.escape(data, quote=False))

    def get_output(self) -> str:
        return "".join(self.output).strip()


def markdown_to_telegram_html(text: str) -> str:
    """
    Converts Markdown text to Telegram-compliant HTML.
    """
    # 1. Convert Markdown to standard HTML
    # fenced_code handles ``` blocks
    raw_html = markdown.markdown(text, extensions=["fenced_code"])

    # 2. Parse and sanitize for Telegram
    parser = TelegramHTMLParser()
    parser.feed(raw_html)
    return parser.get_output()
