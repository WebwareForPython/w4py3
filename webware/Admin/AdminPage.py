import os

from SidebarPage import SidebarPage


class AdminPage(SidebarPage):
    """AdminPage

    This is the abstract superclass of all Webware administration pages.

    Subclasses typically override title() and writeContent(), but may
    customize other methods.
    """

    def cornerTitle(self):
        return 'Webware Admin'

    def writeSidebar(self):
        self.writeAdminMenu()
        self.writeWebwareSidebarSections()

    def writeAdminMenu(self):
        self.menuHeading('Admin')
        self.menuItem('Home', 'Main')
        self.menuItem(
            'Activity log', 'Access', self.fileSize('ActivityLog'))
        self.menuItem(
            'Error log', 'Errors', self.fileSize('ErrorLog'))
        self.menuItem('Config', 'Config')
        self.menuItem('Plug-ins', 'PlugIns')
        self.menuItem('Servlet Cache', 'ServletCache')
        self.menuItem('Application Control', 'AppControl')
        self.menuItem('Logout', 'Main?logout=yes')

    def fileSize(self, log):
        """Utility method for writeMenu() to get the size of a log file.

        Returns an HTML string.
        """
        filename = self.application().setting(log + 'Filename')
        if os.path.exists(filename):
            size = '{:0.0f} KB'.format(os.path.getsize(filename) / 1024)
        else:
            size = 'not existent'
        return f'<span style="font-size:smaller">({size})</span>'

    def loginDisabled(self):
        """Return None if login is enabled, else a message about why not."""
        if self.application().setting('AdminPassword'):
            return None
        return (
            '<p>Logins to admin pages are disabled until'
            ' you supply an AdminPassword in Application.config.</p>')
