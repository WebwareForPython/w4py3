from .ExamplePage import ExamplePage


class PlugInInspector(ExamplePage):
    """Plug-in Inspector.

    Show all the public names of all registered Plug-ins.
    """

    def writeContent(self):
        wr = self.writeln
        for plugIn in self.application().plugIns():
            wr(f'<h4>{self.htmlEncode(plugIn)}</h4>')
            wr('<ul>')
            for name in dir(plugIn):
                if name.startswith('_'):
                    continue
                value = self.htmlEncode(str(getattr(plugIn, name)))
                wr(f'<li><strong>{name}</strong> = {value}</li>')
            self.writeln('</ul>')
