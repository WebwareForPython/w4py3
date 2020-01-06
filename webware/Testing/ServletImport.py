
from Page import Page
import sys

mod_name = __name__  # we expect Testing.ServletImport

class ServletImport(Page):
    """Test of import details."""

    def title(self):
        return self.__doc__

    def writeBody(self):
        self.writeln('<h2>Webware Servlet Import Test</h2>')
        self.writeln(f'<h3>{self.title()}</h3>')
        mod_name_from_class = ServletImport.__module__   # we expect Testing.ServletImport
        mod_name_consistent = mod_name == mod_name_from_class  # we expect True
        servlet_in_sys_modules = mod_name in sys.modules  # we expect True
        servlet_file_watched = __file__ in self.transaction().application()._imp.fileList(update=False)  # we expect True
        self.writeln(
            f"<p>mod_name = <code>{mod_name}</code></p>"
            f"<p>mod_name_from_class = <code>{mod_name_from_class}</code></p>"
            f"<p>mod_name_consistent = <code>{mod_name_consistent}</code></p>"
            f"<p>servlet_in_sys_modules = <code>{servlet_in_sys_modules}</code></p>"
            f"<p>servlet_file_watched = <code>{servlet_file_watched}</code></p>"
        )
