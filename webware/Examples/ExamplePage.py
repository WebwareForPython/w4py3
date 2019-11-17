import os

from SidebarPage import SidebarPage


class ExamplePage(SidebarPage):
    """Webware page template class for displaying examples.

    The convention for picking up examples from Webware plug-ins is:
      * Properties.py must have at least this:
            webwareConfig = {
                'examplePages': []
            }
        But usually specifies various pages:
            webwareConfig = {
                'examplesPages': [
                    'foo',
                    'bar',
                ]
            }
      * The plug-in must have an Examples/ directory.
      * That directory must have an index.* or Main.* which
        inherits from ExamplePage.
      * The implementation can pass in which case a menu of
        the pages for that plug-in is written:
            # Main.py
            from .Examples.ExamplePage import ExamplePage
            class Main(ExamplePage):
                pass

    If webwareConfig['examplesPages'] is non-existent or None, then
    no examples will be available for the plug-in.

    If the Webware Examples context is not present in the first place,
    then there is no access to the plug-in examples.
    """

    def cornerTitle(self):
        return 'Webware Examples'

    def isDebugging(self):
        return False

    def examplePages(self, plugInName=None):
        """Get a list of all example pages.

        Returns a list of all the example pages for our particular plug-in.
        These can be used in the sidebar or in the main content area to
        give easy access to the other example pages.
        """
        if plugInName is None or plugInName == 'Examples':
            # Special case: We're in Webware examples
            from Properties import webwareConfig
            return webwareConfig['examplePages']
        # Any other plug-in:
        try:
            plugIn = self.application().plugIn(plugInName)
        except KeyError:
            return []
        else:
            return plugIn.examplePages()

    def writeSidebar(self):
        self.writeExamplesMenu()
        self.writeOtherMenu()
        self.writeWebwareSidebarSections()

    def writeExamplesMenu(self):
        servletPath = self.request().servletPath()
        self.menuHeading('Examples')
        ctx = self.request().contextName().split('/', 2)
        plugIns = self.application().plugIns()
        plugInName = len(ctx) > 1 and ctx[1] == 'Examples' and ctx[0]
        # Webware
        self.menuItem('Webware', f'{servletPath}/Examples/')
        if not plugInName:
            self.writeExamplePagesItems()
        # Other plug-ins
        for name, plugIn in plugIns.items():
            if plugIn.hasExamplePages():
                link = f'{servletPath}/{plugIn.examplePagesContext()}/'
                self.menuItem(name, link)
                if name == plugInName:
                    self.writeExamplePagesItems(name)

    def writeExamplePagesItems(self, pluginName=None):
        for page in self.examplePages(pluginName):
            self.menuItem(page, page, indentLevel=2)

    def writeOtherMenu(self):
        self.menuHeading('Other')
        self.menuItem(
            'View source of<br>' + self.title(),
            self.request().uriWebwareRoot() + 'Examples/View?filename=' +
            os.path.basename(self.request().serverSidePath()))

    def writeContent(self):
        wr = self.writeln
        wr('<div style="padding-left:22em"><table>')
        for page in self.examplePages(
                self.request().contextName().split('/', 1)[0]):
            wr('<tr><td style="background-color:#e8e8f0">'
               f'<a href={page}>{page}</a></td></tr>')
        wr('</table></div>')
