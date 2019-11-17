from Testing.IncludeURLTest import IncludeURLTest


class IncludeURLTest2(IncludeURLTest):
    """This is the second part of the URL test code.

    It gets included into the IncludeURLTest, and calls methods
    on other servlets to verify the references continue to work.
    """

    def writeBody(self):
        self.writeln('<body style="margin:6pt;font-family:sans-serif">')
        name = self.__class__.__name__
        self.writeln(f'<h2>{name}</h2>')
        module = self.__module__
        self.writeln(f'<h3>class = <code>{name}</code>,'
                     f' module= <code>{module}</code></h3>')
        doc = self.__class__.__doc__.replace('\n\n', '</p><p>')
        self.writeln(f'<p>{doc}</p>')
        self.writeStatus()
        self.cmos(
            "/Testing/", "serverSidePath",
            "Expect to see the serverSidePath of the Testing/Main module.")
        self.writeln('</body>')
