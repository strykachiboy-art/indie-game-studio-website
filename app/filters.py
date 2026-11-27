"""Jinja filters: safe markdown rendering, plain-text excerpts, reading time."""
import html
import re

import markdown as md
import nh3
from markupsafe import Markup

_EXTENSIONS = ["fenced_code", "tables", "sane_lists", "nl2br"]


def _to_html(text: str) -> str:
    return md.markdown(text or "", extensions=_EXTENSIONS)


def render_markdown(text: str) -> Markup:
    """Markdown -> sanitised HTML (scripts, inline handlers, js: links are stripped)."""
    return Markup(nh3.clean(_to_html(text)))


def excerpt(text: str, length: int = 140) -> str:
    """Markdown -> plain text, cut at a word boundary."""
    rendered = re.sub(r"<pre>.*?</pre>", " ", _to_html(text), flags=re.S)
    plain = html.unescape(nh3.clean(rendered, tags=set()))
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= length:
        return plain
    return plain[:length].rsplit(" ", 1)[0].rstrip(",.;:- ") + "…"


def reading_time(text: str) -> str:
    words = len(re.findall(r"\w+", text or ""))
    return f"{max(1, round(words / 200))} min read"


def register_filters(app):
    app.add_template_filter(render_markdown, "markdown")
    app.add_template_filter(excerpt, "excerpt")
    app.add_template_filter(reading_time, "reading_time")
