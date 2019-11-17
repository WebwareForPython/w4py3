from os.path import exists, splitext

from .AdminSecurity import AdminSecurity


class View(AdminSecurity):
    """View a text or html file.

    The Admin View servlet loads any text or html file
    in your application working directory on the Webware server
    and displays it in the browser for your viewing pleasure.
    """

    def defaultAction(self):
        self._data = self._type = None
        self.writeHTML()
        if self._data and self._type:
            try:
                response = self.response()
                response.reset()
                response.setHeader('Content-Type', self._type)
                self.write(self._data)
            except Exception:
                self.writeError('File cannot be viewed!')

    def writeError(self, message):
        self.writeln(
            f'<h3 style="color:red">Error</h3><p>{message}</p>')

    def writeContent(self):
        filename = self.request().field('filename', None)
        if not filename:
            self.writeError('No filename given to view!')
            return
        filename = self.application().serverSidePath(filename)
        if not exists(filename):
            self.writeError(
                f'The requested file {filename!r} does not exist'
                ' in the server side directory.')
            return
        self._type = 'text/' + (
            'html' if splitext(filename)[1] in ('.htm', '.html') else 'plain')
        try:
            with open(filename) as f:
                self._data = f.read()
        except Exception:
            self.writeError(f'The requested file {filename!r} cannot be read.')
