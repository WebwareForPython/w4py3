from Page import Page

# Set this to True if you want to pass additional information.
# For security reasons, this has been disabled by default.
appInfo = False


class EditFile(Page):
    """Helper for the feature provided by the IncludeEditLink setting."""

    def writeInfo(self, key, value):
        self.writeln(f'{key}: {value}')

    def writeHTML(self):
        res = self.response()
        header = res.setHeader
        info = self.writeInfo
        req = self.request()
        env = req.environ()
        field = req.field

        header('Content-Type', 'application/x-webware-edit-file')
        header('Content-Disposition', 'inline; filename="Webware.EditFile"')

        # Basic information for editing the file:
        info('Filename', field('filename'))
        info('Line', field('line'))

        # Additional information about the hostname:
        info('Hostname', env.get('HTTP_HOST', 'localhost'))

        if appInfo:
            # Additional information about this Webware installation:
            app = self.application()
            info('ServerSidePath', app.serverSidePath())
            info('WebwarePath', app.webwarePath())
