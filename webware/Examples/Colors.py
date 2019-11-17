from .ExamplePage import ExamplePage

# Helper functions

gamma = 2.2  # an approximation for today's CRTs


def brightness(r, g, b):
    """Calculate brightness of RGB color."""
    r, g, b = [x / 255.0 for x in (r, g, b)]
    return (0.3*r**gamma + 0.6*g**gamma + 0.1*b**gamma)**(1/gamma)


def textColorForRgb(r, g, b):
    """Determine a good text font color for high contrast."""
    return 'white' if brightness(r, g, b) < 0.5 else 'black'


def rgbToHexColor(r, g, b):
    """Convert r, g, b to #RRGGBB."""
    return f'#{int(r):02X}{int(g):02X}{int(b):02X}'


def hexToRgbColor(h):
    """Convert #RRGGBB to r, g, b."""
    h = h.strip()
    if h.startswith('#'):
        h = h[1:]
    h = h[:2], h[2:4], h[4:]
    return [int(x, 16) for x in h]


def colorTable():
    """Prepare HTML for the color table"""
    numSteps = 6  # this gives the "web-safe" color palette
    steps = [255.0 * x / (numSteps - 1) for x in range(numSteps)]
    table = [
        '<p>Click on one of the colors below to set the background color.</p>',
        '<table style="margin-left:auto;margin-right:auto">']
    for r in steps:
        for g in steps:
            table.append('<tr>')
            for b in steps:
                bgColor = rgbToHexColor(r, g, b)
                textColor = textColorForRgb(r, g, b)
                table.append(
                    f'<td style="background-color:{bgColor};color:{textColor}"'
                    f' onclick="document.forms[0].bgColor.value=\'{bgColor}\';'
                    f'document.forms[0].submit()">{bgColor}</td>')
            table.append('</tr>')
    table.append('</table>')
    return '\n'.join(table)


class Colors(ExamplePage):
    """Colors demo.

    This class is a good example of caching. The color table that
    this servlet creates never changes, so the servlet caches this
    in the _colorTable class attribute. The original version of this
    example did no caching and was 12 times slower.
    """

    _colorTable = colorTable()

    def htBodyArgs(self):
        """Write the attributes of the body element.

        Overridden in order to throw in the custom background color
        that the user can specify in our form.
        """
        self._bgColor = self.request().field('bgColor', '#FFFFFF')
        try:
            r, g, b = hexToRgbColor(self._bgColor)
            self._textColor = textColorForRgb(r, g, b)
        except Exception:
            self._textColor = 'black'
        return f'style="color:black;background-color:{self._bgColor}"'

    def writeContent(self):
        """Write the actual content of the page."""
        self.write(f'''
            <div style="text-align:center;color:{self._textColor}">
            <h3>Color Table Demo</h3>
            <form action="Colors" method="post">
                <label for="bgColor">Background color:</label>
                <input type="text" name="bgColor" id="bgColor"
                       value="{self._bgColor}">
                <input type="submit" value="Go">
            </form>
            {self._colorTable}
            </div>
            ''')
