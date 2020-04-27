from math import sin, pi

from io import BytesIO

from MiscUtils.Funcs import asclocaltime
from .ExamplePage import ExamplePage

try:
    from PIL import Image as pilImage, ImageDraw, ImageFont
except ImportError:
    pilImage = ImageDraw = ImageFont = None


w, h = 500, 200  # the image size


def t(p):
    """Map coordinates: (x=0..2pi, y=-1.25..1.25) => (0..X, Y..0)"""
    return int(.5 * w * p[0] / pi + .5), int(.4 * h * (1.25 - p[1]) + .5)


colors = (255, 255, 255), (0, 0, 0), (0, 0, 255), (255, 0, 0)
white, black, blue, red = range(4)


class Drawing:
    """Simple wrapper class for drawing the example image."""

    def __init__(self):
        self._image = pilImage.new('RGB', (w, h), colors[white])
        self._draw = ImageDraw.Draw(self._image)
        for font in 'Tahoma Verdana Arial Helvetica'.split():
            try:
                font = ImageFont.truetype(font + '.ttf', 12)
            except (AttributeError, IOError):
                font = None
            if font:
                break
        else:
            try:
                font = ImageFont.load_default()
            except (AttributeError, IOError):
                font = None
        self._font = font

    def text(self, pos, string, color):
        color = colors[color]
        self._draw.text(t(pos), string, color, font=self._font)

    def lines(self, points, color):
        color = colors[color]
        self._draw.line(list(map(t, points)), color)

    def png(self):
        s = BytesIO()
        self._image.save(s, 'png')
        return s.getvalue()


class ImageDemo(ExamplePage):
    """Dynamic image generation example.

    This example creates an image of a sinusoid.

    For more information on generating graphics, see
    https://wiki.python.org/moin/GraphicsAndImages.

    This example uses the Python Imaging Library (Pillow).
    """

    saveToFile = False

    def defaultAction(self):
        fmt = self.request().field('fmt', None)
        if fmt == '.png' and pilImage:
            image = self.generatePNGImage()
            res = self.response()
            res.setHeader("Content-Type", "image/png")
            res.setHeader("Content-Length", str(len(image)))
            if self.saveToFile:
                res.setHeader("Content-Disposition",
                              "attachment; filename=demo.png")
            self.write(image)
        else:
            self.writeHTML()

    def writeContent(self):
        wr = self.writeln
        wr('<h2>Webware Image Generation Demo</h2>')
        lib = 'Python Imaging Library (Pillow)'
        if pilImage:
            wr('<img src="ImageDemo?fmt=.png" alt="Generated example image"'
               f' width="{w:d}" height="{h:d}">')
            wr(f'<p>This image has just been generated using the {lib}.</p>')
        else:
            wr('<h4 style="color:red">Sorry: No imaging tool available.</h4>')
            src = 'https://pypi.org/project/Pillow/'
            wr(f'<p>This example requires the <a href="{src}">{lib}</a>.</p>')

    def generatePNGImage(self):
        """Generate and return a PNG example image."""
        def f(x):
            return x, sin(x)
        draw = Drawing()
        draw.text((2.7, 0.8), 'y=sin(x)', black)
        draw.text((0.2, -0.8), f'created: {asclocaltime()}', red)
        draw.lines(((0, 0), (2 * pi, 0)), black)  # x-axis
        draw.lines(((0, -1), (0, 1)), black)  # y-axis
        draw.lines([f(x * 2 * pi / w) for x in range(w + 1)], blue)
        return draw.png()
