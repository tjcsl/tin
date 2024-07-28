from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from django.http import HttpResponse

__all__ = ["Html"]


class Html:
    """A wrapper around BeautifulSoup to make it easier to test html content.

    For advanced usage, you can access the BeautifulSoup object directly via
    :attr:`.Html.soup`.

    Examples:

        .. code-block:: pycon

            >>> raw_html = \"\"\"
            ... <button><a href='example.org'>Hi!</a></button>
            ... <input type="submit" value="Blame the compiler">
            ... <p>switch your major to PHYSICS!</p>
            ... <a href="example.org"><button>Rust Forever!</button></a>
            ... \"\"\"
            >>> html = Html(raw_html)
            >>> html.has_button("Hi!")
            True
            >>> html.has_button(href="example.org")
            True
            >>> html.has_button("Rust Forever!", href="example.org")
            True
            >>> html.has_button("Rust Forever!", href="example.com")
            False
            >>> html.has_text("switch your MAJOR to physics!")
            True
            >>> html.has_text("switch your MAJOR to physics!", case_sensitive=True)
            False
    """

    def __init__(self, html: str) -> None:
        self.soup = BeautifulSoup(html, "lxml")

    @classmethod
    def from_response(cls, response: HttpResponse):
        """Create an Html object from a Django :class:`~django.http.HttpResponse`.

        Examples:

            .. code-block:: pycon

                >>> from django.http import HttpResponse
                >>> response = HttpResponse("<p>Hi!</p>")
                >>> html = Html.from_response(response)
                >>> html.has_text("Hi!")
                True

        """
        return cls(response.content.decode("utf-8"))

    def has_button(self, text: str | None = None, *, href: str | None = None) -> bool:
        """Check if a submit button with the correct properties exists.

        .. warning::

            This will not match against ``<input type="not submit">`` tags.

        Args:
            text: The text of the button. If not provided, it will not be checked.
            href: The url the button links to. If not provided, it will not be checked.

        Examples:

            .. code-block:: pycon

                >>> raw_html = '''
                ... <button>Hi!</button>
                ... <input type="submit" value="Blame the compiler">
                ... '''
                >>> html = Html(raw_html)
                >>> html.has_button()
                True
                >>> html.has_button("Hi!")
                True
                >>> html.has_button("Blame the compiler")
                True
                >>> html.has_button("Blame the compiler", href="https://example.com")
                False
                >>> html.has_button(href="https://example.com")
                False
        """
        buttons = self.soup("button")
        # assume <input type="submit"> is a button
        inputs = self.soup("input", type="submit")

        tin_btns = self.soup("a", class_="tin-btn")

        # if no arguments are provided, check if any button exists
        if text is None and href is None:
            # "or" returns the first value if it's truthy otherwise the second value
            # so we have to bool() it to make typecheckers happy
            return bool(buttons or inputs or tin_btns)

        return (
            any(_check_tin_button(btn, text=text, href=href) for btn in tin_btns)
            or any(_check_button(btn, text=text, href=href) for btn in buttons)
            or any(_check_input_tag(input_, text=text, href=href) for input_ in inputs)
        )

    def has_text(self, text: str, case_sensitive: bool = False) -> bool:
        """Check if a piece of text is present inside the html.

        .. note::

            This will only match against text, not content inside tags.

        .. warning::

            Be careful with the matching text. For example, trying to match
            ``"hi"`` would result in a false positive for the text ``"this"``.

        Examples:

            .. code-block:: pycon

                >>> raw_html = '''
                ... <p class="insideTag">This is a really long sentence</p>
                ... '''
                >>> html = Html(raw_html)
                >>> html.has_text("REALLY long sentence")
                True
                >>> html.has_text("REALLY long sentence", case_sensitive=True)
                False
                >>> html.has_text("really long sentence", case_sensitive=True)
                True
                >>> html.has_text("insideTag")
                False
        """

        def string_filter(s: str) -> bool:
            return text in s if case_sensitive else text.lower() in s.lower()

        return self.soup.find(string=string_filter) is not None


def _check_tin_button(button, *, text: str | None = None, href: str | None = None) -> bool:
    if text is not None and button.text != text:
        return False
    return href is None or button.get("href") == href


def _check_button(button, *, text: str | None = None, href: str | None = None) -> bool:
    """Check if a button has the correct properties."""
    if text is not None and button.text != text:
        return False
    return (
        href is None
        or button.find_parent("a", href=href) is not None
        or button.find("a", href=href) is not None
    )


def _check_input_tag(input, *, text: str | None = None, href: str | None = None) -> bool:
    """Check if an input tag has the correct properties"""
    if text is not None and input.get("value") != text:
        return False

    return (
        href is None
        or input.find_parent("a", href=href) is not None
        or input.find("a", href=href) is not None
    )
