from Page import Page


class Servlet(Page):
    """Test of extra path info."""

    def title(self):
        return self.__doc__

    def writeBody(self):
        self.writeln('<h2>Webware Testing Servlet</h2>')
        self.writeln(f'<h3>{self.title()}</h3>')
        req = self.request()
        self.writeln(
            f"<p>serverSidePath = <code>{req.serverSidePath()}</code></p>")
        self.writeln(
            f"<p>extraURLPath = <code>{req.extraURLPath()}</code></p>")
