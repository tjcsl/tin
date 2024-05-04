from pygments.formatters import HtmlFormatter


class HtmlCodeFormatter(HtmlFormatter):
    def __init__(self, lang_str: str = '', **kwargs):
        super().__init__(**kwargs)
        # lang_str has the value {lang_prefix}{lang}
        # specified by the CodeHilite's options
        self.lang_str = lang_str

    def _wrap_code(self, source):
        yield 0, f'<code class="{self.lang_str}">'
        yield from source
        yield 0, '</code>'
