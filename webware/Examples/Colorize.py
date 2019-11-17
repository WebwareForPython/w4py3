import os

from Page import Page

try:
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatters import HtmlFormatter
except ImportError:
    highlight = None

errorPage = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Error</title>
<style>
body {{ font-family:sans-serif; font-size:16px; }}
</style>
</head>
<body>
<h3 style="color:#a00">Error</h3>
<p>{}</p>
</body>
</html>
"""

viewPage = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{}</title>
<style>{}</style>
</head>
<body class="highlight">
{}
</body>
</html>
"""


class Colorize(Page):
    """Syntax highlights Python source files."""

    def respond(self, transaction):
        """Write out a syntax highlighted version of the file."""
        res = transaction._response
        req = self.request()
        if not req.hasField('filename'):
            res.write(errorPage.format('No filename given to syntax color!'))
            return
        filename = req.field('filename')
        filename = self.request().serverSidePath(os.path.basename(filename))
        try:
            with open(filename) as f:
                source = f.read()
        except IOError:
            source = None
        if source is None:
            res.write(errorPage.format(
                f'The requested file {os.path.basename(filename)!r}'
                ' does not exist in the proper directory.'))
            return
        if highlight:
            formatter = HtmlFormatter()
            lexer = PythonLexer()
            output = highlight(source, lexer, formatter)
            style = formatter.get_style_defs('.highlight')
            output = viewPage.format(filename, style, output)
        else:
            print("Pygments highlighter not found - showing plain source")
            res.setHeader('Content-Type', 'text/plain')
            output = source
        res.write(output)
