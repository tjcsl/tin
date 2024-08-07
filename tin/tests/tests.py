from __future__ import annotations

import pytest

from .ui_testing import Html


def test_html_has_button_no_href():
    raw_html = """
    <button>Hi!</button>
    <input type="submit" value="Blame the compiler">
    """
    html = Html(raw_html)
    # with no arguments it should raise a ValueError
    with pytest.raises(ValueError, match="At least one of text or href must be provided"):
        html.has_button()
    assert html.has_button("Hi!")
    # has button is case insensitive
    assert html.has_button("hi!")
    assert html.has_button("Blame the compiler")

    raw_html = """
    <buttn></buttn>
    <input type="list" value="Blame the compiler">
    """
    html = Html(raw_html)
    assert not html.has_button("Blame the compiler")


def test_html_has_button_with_href():
    raw_html = """
    <button><a href="https://example.com">Hi!</a></button>
    <input type="submit" value="Blame the compiler">
    <a href='https://google.com'><button>Google</button></a>
    <a class="bob tin-btn" href="https://example.com">Bob</a>
    """
    html = Html(raw_html)
    assert html.has_button(href="https://example.com")
    assert not html.has_button(href="https://example.org")
    assert html.has_button("Google", href="https://google.com")
    # should also search for <a class="tin-btn"
    assert html.has_button("Bob", href="https://example.com")
    raw_html = """
    <button>Hi!</button>
    <input type="submit" value="Blame the compiler">
    """
    html = Html(raw_html)
    assert not html.has_button(href="https://example.com")


def test_has_text():
    raw_html = '<p class="insideTag">This is a really long sentence</p>'
    html = Html(raw_html)

    # it should be case insensitive by default
    assert html.has_text("REALLY long sentence")

    assert not html.has_text("REALLY long sentence", case_sensitive=True)
    assert html.has_text("really long sentence", case_sensitive=True)

    assert not html.has_text("insideTag")
