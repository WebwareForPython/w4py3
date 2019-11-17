from Page import Page


class EmbeddedServlet(Page):
    """Test extra path info.

    This servlet serves as a test for "extra path info"-style URLs such as:

        http://localhost/Webware/Servlet/Extra/Path/Info

    Where the servlet is embedded in the URL, rather than being the last
    component. This servlet simply prints its fields.
    """

    def writeBody(self):
        fields = self.request().fields()
        self.writeln('<h2>EmbeddedServlet</h2>')
        self.writeln(f'<pre>{self.__class__.__doc__}</pre>')
        self.writeln(f'<h3>Fields: {len(fields)}</h3>')
        self.writeln('<ul>')
        enc = self.htmlEncode
        for key, value in fields.items():
            self.writeln(f'<li>{enc(key)} = {enc(value)}</li>')
        self.writeln('</ul>')
