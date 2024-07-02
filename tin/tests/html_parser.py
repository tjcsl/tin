from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pprint import pformat
from typing import TYPE_CHECKING

__all__ = (
    "HTMLElement",
    "Parser",
)


if TYPE_CHECKING:
    from django.http import HttpResponse
    from typing_extensions import Self, TypeVar

    T = TypeVar("T", bound="Parser")


@dataclass(frozen=True)
class HTMLElement:
    """An HTML Element.

    Stores the name of the tag, and it's attribute information.
    Normal text/data is represented as a tag with no attributes.

    Args:
        tag : the html tag
        attrs : attributes of the element
        is_text : whether the tag is the data
    """

    # TODO: after python 3.11 pass slots=True to @dataclass
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    is_text: bool = False


class EndingElement(HTMLElement):
    """The ending tag of an html element."""

    def __init__(self, tag: str) -> None:
        super().__init__(tag, attrs={}, is_text=False)


class Parser(HTMLParser):
    """A list of every element in the HTML.

    Does not include comments or other metadata.

    Examples:

        .. code-block:: pycon

            >>> parser = Parser.from_html(
            ...     '<html><head><title>Test</title></head><body><h1 style="color:red">Parse me!</h1></body></html>'
            ... )
            >>> parser.contains_tag("h1")  # check if the tag h1 is in the html
            True
            >>> "h1" in parser  # checks if the text h1 is in the html
            False
            >>> parser @ "h1"  # get the element <h1>
            HTMLElement(tag='h1', attrs={'style': 'color:red'}, is_text=False)
            >>> "Parse me!" in parser
            True
            >>> parser.contains_tag("h3")
            False
            >>> element = HTMLElement("h1", {"style": "color:red"})
            >>> parser.contains(element)
            True
            >>> parser.reset()
            >>> parser.contains_tag("h1")
            False

        You can also construct an instance from a :class:`~django.http.HttpResponse`:

        .. code-block::

            @login("teacher")
            def test_show_view(client, course):
                response = client.get(reverse("courses:index"))
                parser = Parser.from_response(response)
                assert parser.contains_tag(course.name)


        The content of ``<script></script>`` and ``<style></style>`` are NOT processed further, and are instead stored as the ``content``
        attribute on the script/style element.

        .. code-block:: pycon

            >>> html = "<script>alert('<h1>hi</h1>')</script>"
            >>> parser = Parser.from_html(html)
            >>> parser.contains_tag("h1")
            False
            >>> parser @ "script"
            HTMLElement(tag='script', attrs={'content': "alert('<h1>hi</h1>')"}, is_text=False)

    .. hint::

        You can access each :class:`.HTMLElement` in the html via :attr:`elements`.
    """

    @property
    def elements(self) -> list[HTMLElement]:
        """Every parsed element in the HTML"""
        return self._elements

    # parsing methods
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Handle a tag starting.

        .. warning::

            This is an implementation detail.
        """
        if tag in ("script", "style"):
            self._attach_to_previous_elem = True
        self._elements.append(HTMLElement(tag, attrs=dict(attrs)))

    def handle_data(self, data: str) -> None:
        """Handle data, e.g. text nodes and ``<script></script>`` nodes.

        .. warning::

            This is an implementation detail.
        """
        # if it's a script or style block, attach it to the previous
        # with the content attribute
        if self._attach_to_previous_elem:
            self.elements[-1].attrs.update({"content": data})
            self._attach_to_previous_elem = False
        else:
            self._elements.append(HTMLElement(tag=data, is_text=True))

    def handle_endtag(self, tag: str) -> None:
        self._elements.append(EndingElement(tag))

    def reset(self) -> None:
        """Reset the parser"""
        self._elements = []
        self._attach_to_previous_elem = False
        return super().reset()

    # user space
    @classmethod
    def from_html(cls: type[T], html: str) -> T:
        """Construct a parsed instance of :class:`Parser` from some html."""
        parser = cls()
        parser.feed(html)
        return parser

    @classmethod
    def from_response(cls: type[T], response: HttpResponse) -> T:
        """Construct a parsed instance of :class:`Parser` from an :class:`~django.http.HttpResponse`."""
        html = response.content.decode("utf-8")
        return cls.from_html(html)

    def contains_tag(self, tag: str) -> bool:
        """Check if a tag is in the parsed data"""
        return self.contains(HTMLElement(tag))

    def contains_text(self, txt: str) -> bool:
        """Check if some text is present in the HTML.

        .. code-block:: pycon

            >>> html = Parser.from_html("<div>Say hi!</div>")
            >>> html.contains_text("div")
            False
            >>> html.contains_text("Say hi!")
            True
        """
        return any(txt in item.tag for item in self.elements if item.is_text)

    def contains(self, element: HTMLElement) -> bool:
        """Checks if a :class:`HTMLElement` is in the HTML.

        This does not check if the element matches exactly (only the tag must match exactly).
        Instead, it checks if all of the attributes of ``element``
        are contained within any html element.

        This is useful if for example you don't want styling changes
        to break tests.

        .. code-block:: pycon

            >>> parser = Parser.from_html('<img src="/static/img/hi.png" style="color:red">')
            >>> full_element = HTMLElement("img", {"src": "/static/img/hi.png", "style": "color:red"})
            >>> parser.contains(full_element)  # prefer parser.contains_exact for speed
            True
            >>> partial_element = HTMLElement("img", {"src": "/static/img/hi.png"})
            >>> parser.contains(partial_element)
            True
        """
        tag = element.tag
        items = element.attrs.items()
        return any(
            elem.tag == tag and items <= elem.attrs.items()
            for elem in self.elements
            if not elem.is_text
        )

    def contains_href(self, text: str, link: str | None = None) -> bool:
        """Checks for an ``<a></a>`` tag that links to ``link``, and has the text ``text`` inside.

        .. code-block:: pycon

            >>> html = Parser.from_html('<a><span style="color:red">Submit</span></a>')
            >>> html.contains_href("Submit")
            True

        .. warning::

            This does not behave well with invalid html. For example, the following would
            give a false positive::

                >>> html = Parser.from_html("<a><a>Hi</a>")
                >>> html.contains_href("Hi")
                True
        """
        for idx, element in enumerate(self.elements):
            # check if it's a hyperlink (note: this fails for nested <a>)
            if not (element.tag == "a" and element.attrs.get("href") == link):
                continue

            # first find the closing </a>
            # then check every element in between for the specified text
            ending = EndingElement("a")

            # possibly due to invalid html
            if ending not in self._elements[idx + 1 :]:
                continue

            end_idx = self._elements.index(EndingElement("a"), idx + 1)
            # check every element between the next element and the closing
            # tag to see if they contain the specified text.
            if any(elem.is_text and elem.tag == text for elem in self.elements[idx + 1 : end_idx]):
                return True
        return False

    __contains__ = contains_text

    def copy(self) -> Self:
        """Shallow copy a :class:`Parser`"""
        parser = type(self)()
        parser._elements = self._elements.copy()
        return parser

    __copy__ = copy

    def __matmul__(self, tag: str) -> HTMLElement:
        if not isinstance(tag, str):
            raise NotImplementedError("Can only get element by tag!")
        element = next(
            (elem for elem in self.elements if elem.tag == tag and not elem.is_text), None
        )
        if element is None:
            raise IndexError(f"Could not find tag {tag}")
        return element

    def __iter__(self):
        return iter(self.elements)

    def __str__(self) -> str:
        return type(self).__name__

    def __repr__(self) -> str:
        result = str(self)
        if self.elements:
            result += f" of\n{pformat(self.elements)}"
        return result
