"""Webware page template class for pages with a sidebar."""

from Page import Page


class SidebarPage(Page):
    """Webware page template class for pages with a sidebar.

    SidebarPage is an abstract superclass for pages that have a sidebar
    (as well as a header and "content well"). Sidebars are normally used
    for navigation (e.g., a menu or list of links), showing small bits
    of info and occasionally a simple form (such as login or search).

    Subclasses should override cornerTitle(), writeSidebar() and
    writeContent() (and title() if necessary; see Page).

    The utility methods menuHeading() and menuItem() can be used by
    subclasses, typically in their implementation of writeSidebar().

    Webware itself uses this class: Examples/ExamplePage and Admin/AdminPage
    both inherit from it.
    """

    # region StyleSheet

    _styleSheet = '''
html {
  height: 100%;
}
body {
  background-color: white;
  color: #080810;
  font-size: 11pt;
  font-family: Tahoma,Verdana,Arial,Helvetica,sans-serif;
  margin: 0;
  padding: 0;
  height: 100%;
}
h1 { font-size: 18pt; }
h2 { font-size: 16pt; }
h3 { font-size: 14pt; }
h4 { font-size: 12pt; }
h5 { font-size: 11pt; }
#Page {
  display: table;
  width: 100%;
  height: 100%;
}
#Page > div {
  display: table-row;
}
#Page > div > div {
  display: table-cell;
}
#CornerTitle {
  background-color: #101040;
  color: white;
  padding: 6pt 6pt;
  font-size: 14pt;
  text-align: center;
  vertical-align: middle;
}
#Banner {
  background-color: #202080;
  color: white;
  padding: 8pt 6pt;
  font-size: 16pt;
  font-weight: bold;
  text-align: center;
  vertical-align: middle;
}
#Sidebar {
    background-color: #e8e8f0;
    padding: 4pt;
    font-size: 10pt;
    line-height: 13pt;
    vertical-align: top;
    white-space: nowrap;
    height: 100%;
}
#Sidebar div {
    margin-bottom: 1pt;
}
#Sidebar div.MenuHeading {
    font-weight: bold;
    margin-top: 6pt;
    margin-bottom: 3pt;
    width: 12em;
}
#Content {
    padding: 8pt;
    vertical-align: top;
    width: 100%;
}
table.NiceTable {
    margin-bottom: 4pt;
}
table.NiceTable td, .Data {
    background-color: #eee;
    color: #111;
}
table.NiceTable th {
    text-align: left;
}
table.NiceTable tr.TopHeading th {
    text-align: center;
}
table tr th, .SubHeading {
    background-color: #ccc;
    color: black;
}
table tr.TopHeading th, .TopHeading {
background-color: #555;
color: white;
}
#Content table tr.NoTable td {
    background-color: white;
    color: #080810;
}
table.NiceTable th a:link, table.NiceTable th a:visited {
    color: #101040;
}
'''

    def writeStyleSheet(self):
        """We're using a simple internal style sheet.

        This way we avoid having to care about where an external style
        sheet should be located when this class is used in another context.
        """
        self.writeln(f'<style>{self._styleSheet}</style>')

    # endregion StyleSheet

    # region Content methods

    def writeBodyParts(self):
        wr = self.writeln
        wr('<div id="Page"><div>')
        self.writeBanner()
        wr('</div><div><div id="Sidebar">')
        self.writeSidebar()
        wr('</div><div id="Content">')
        self.writeContent()
        wr('</div></div></div>')

    def writeBanner(self):
        self.writeln(
            f'<div id="CornerTitle">{self.cornerTitle()}</div>',
            f'<div id="Banner">{self.title()}</div>')

    def writeSidebar(self):
        self.writeWebwareSidebarSections()

    @staticmethod
    def cornerTitle():
        return ''

    # endregion Content methods

    # region Menu

    def menuHeading(self, title):
        self.writeln(f'<div class="MenuHeading">{title}</div>')

    def menuItem(self, title, url=None, suffix=None, indentLevel=1):
        if url is not None:
            title = f'<a href="{url}">{title}</a>'
        if suffix:
            title += ' ' + suffix
        margin = 4 * indentLevel
        self.writeln(f'<div style="margin-left:{margin}pt">{title}</div>')

    # endregion Menu

    # region Sidebar

    def writeWebwareSidebarSections(self):
        """Write sidebar sections.

        This method (and consequently the methods it invokes)
        are provided for Webware's example and admin pages.
        It writes sections such as contexts, e-mails, exits and versions.
        """
        self.writeContextsMenu()
        self.writeWebwareEmailMenu()
        self.writeWebwareExitsMenu()
        self.writeVersions()

    def writeContextsMenu(self):
        self.menuHeading('Contexts')
        servletPath = self.request().servletPath()
        contexts = sorted(
            ctx for ctx in self.application().contexts()
            if ctx != 'default' and '/' not in ctx)
        for context in contexts:
            self.menuItem(context, f'{servletPath}/{context}/')

    def writeWebwareEmailMenu(self):
        self.menuHeading('E-mail')
        self.menuItem(
            'webware-discuss', 'mailto:webware-discuss@lists.sourceforge.net')

    def writeWebwareExitsMenu(self):
        self.menuHeading('Exits')
        self.menuItem('Webware', 'https://webwareforpython.github.io/w4py3/')
        self.menuItem('Python', 'https://www.python.org/')

    def writeVersions(self):
        app = self.application()
        self.menuHeading('Versions')
        self.menuItem('Webware ' + app.webwareVersionString())
        from sys import version
        self.menuItem('Python ' + version.split(None, 1)[0])

    def writeContent(self):
        self.writeln('Woops, someone forgot to override writeContent().')

    # endregion Sidebar
