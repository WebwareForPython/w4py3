from Page import Page


class IncludeMe(Page):

    def writeHTML(self):
        self.writeln('<h1>Hello from IncludeMe</h1>')
        self.writeln('<p>I like to be included. This is my content.</p>')
