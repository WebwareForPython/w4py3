from .ExamplePage import ExamplePage


class Introspect(ExamplePage):

    def writeContent(self):
        self.writeln('<h4>Introspection</h4>')
        self.writeln(
            "<p>The following table shows the values for various Python"
            " expressions, all of which are related to <em>introspection</em>."
            " That is to say, all the expressions examine the environment such"
            " as the object, the object's class, the module and so on.</p>")
        self.writeln('<table style="width:100%;background-color:#eef">')
        self.list('list(locals())')
        self.list('list(globals())')
        self.list('dir(self)')
        self.list('dir(self.__class__)')
        self.list('self.__class__.__bases__')
        self.list('dir(self.__class__.__bases__[0])')
        self.writeln('</table>')

    def pair(self, key, value):
        if isinstance(value, (list, tuple)):
            value = ', '.join(map(str, value))
        value = self.htmlEncode(str(value))
        self.writeln(
            '<tr style="vertical-align:top">'
            f'<td>{key}</td><td>{value}</td></tr>')

    def list(self, codeString):
        value = eval(codeString)
        if not isinstance(value, (list, tuple)):
            value = '<em>not a list or a tuple</em>'
        self.pair(codeString, value)
