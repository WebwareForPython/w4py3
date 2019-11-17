from Page import Page


class Simple(Page):

    def writeContent(self):
        self.writeln('<h1>Simple Servlet</h1>')
        self.writeln('<p>This is a very simple servlet.</p>')
