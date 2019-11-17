try:
    import dominate
except ImportError:
    dominate = None
else:
    from dominate.tags import a, div, h2, p, table, tbody, td, th, tr
    from dominate.util import text

from .ExamplePage import ExamplePage


class DominateDemo(ExamplePage):
    """Demo for using the Dominate library."""

    homepage = 'https://github.com/Knio/dominate'

    def writeContent(self):
        self.writeln('<h1>Using Webware with Dominate</h1>')
        self.writeln(
            '<p>Dominate is a Python library that can be used in Webware'
            ' applications to generate HTML programmatically.</p>')
        if not dominate:
            self.writeln(
                f'<p>Please install <a href="{self.homepage}">Dominate</a>'
                ' in order to view this demo.</p>')
            return

        content = div(id='content')
        with content:
            h2('Hello World!')
            with table(cls="NiceTable").add(tbody()):
                tr(th('Demo table', colspan=3))
                r = tr()
                r += td('One')
                r.add(td('Two'))
                with r:
                    td('Three')
            para = p(__pretty=False)
            with para:
                text('This content has been produced with ')
                a('Dominate', href=self.homepage)
                text(' programmatically.')
        self.write(content)
