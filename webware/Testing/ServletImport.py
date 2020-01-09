import sys

from SidebarPage import SidebarPage

modName = __name__  # should be Testing.ServletImport


class ServletImport(SidebarPage):
    """Test of servlet import details."""

    def cornerTitle(self):
        return 'Testing'

    def writeContent(self):
        wr = self.writeln
        wr('<h2>Webware Servlet Import Test</h2>')
        wr(f'<h3>{self.__doc__}</h3>')
        modNameFromClass = ServletImport.__module__
        modNameConsistent = modName == modNameFromClass
        servletInSysModules = modName in sys.modules
        app = self.transaction().application()
        files = app._imp.fileList(update=False)
        servletFileWatched = __file__ in files
        wr(
            f"<p>modName = <code>{modName}</code></p>"
            f"<p>modNameFromClass = <code>{modNameFromClass}</code></p>"
            f"<p>modNameConsistent = <code>{modNameConsistent}</code></p>"
            f"<p>servletInSysModules = <code>{servletInSysModules}</code></p>"
            f"<p>servletFileWatched = <code>{servletFileWatched}</code></p>"
        )
        ok = modNameConsistent and servletInSysModules and servletInSysModules
        wr('<p style="color:{}"><b>Servlet import test {}.</b></p>'.format(
            'green' if ok else 'red', 'passed' if ok else 'failed'))
