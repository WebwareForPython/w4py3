import time
import http.client

from SidebarPage import SidebarPage


class TestIMS(SidebarPage):

    def cornerTitle(self):
        return 'Testing'

    def error(self, msg):
        self.write(f'<p style="color:red">{self.htmlEncode(msg)}</p>')

    def writeMsg(self, msg):
        self.write(f'<p>{self.htmlEncode(msg)}</p>')

    def writeTest(self, msg):
        self.write(f'<h4>{msg}</h4>')

    def getDoc(self, path, headers=None):
        if headers is None:
            headers = {}
        con = self._httpConnection(self._host)
        con.request('GET', path, headers=headers)
        return con.getresponse()

    def writeContent(self):
        self.writeln('<h2>Test If-Modified-Since support in Webware</h2>')
        if self.request().environ().get('paste.testing'):
            self.writeln('<p>This test requires a running web server.</p/>')
            return
        d = self.request().serverDictionary()
        self._host = d['HTTP_HOST']  # includes the port
        self._httpConnection = (
            http.client.HTTPSConnection if d.get('wsgi.url_scheme') == 'https'
            else http.client.HTTPConnection)
        servletPath = self.request().servletPath()
        # pick a static file which is served up by Webware's UnknownFileHandler
        self.runTest(f'{servletPath}/PSP/Examples/psplogo.png')

    def runTest(self, path):
        self.writeTest(f'Opening <code>{path}</code>')
        rsp = self.getDoc(path)
        originalSize = size = len(rsp.read())
        if rsp.status != 200:
            self.error(f'Expected status of 200, received {rsp.status}.')
            return
        if size > 0:
            self.writeMsg(
                f'Received: {rsp.status} rsp.reason{rsp.reason},'
                f' document size = {size} (as expected).')
        else:
            self.error(f'Document size is: {size}')
            return
        lastMod = rsp.getheader('Last-Modified', '')
        if lastMod:
            self.writeMsg(f'Last modified: {lastMod}')
        else:
            self.error('No Last-Modified header found.')
            return
        # Retrieve document again with IMS and expect a 304 not modified
        self.writeTest(
            f'Opening <code>{path}</code><br>'
            f'with If-Modified-Since: {lastMod}')
        rsp = self.getDoc(path, {'If-Modified-Since': lastMod})
        size = len(rsp.read())
        if rsp.status != 304:
            self.error(f'Expected status of 304, received {rsp.status}.')
            return
        if size:
            self.error(f'Expected 0 length document, received {size} bytes.')
            return
        self.writeMsg(
            f'Received {rsp.status} {rsp.reason},'
            f' document size = {size} (as expected).')
        arpaFormat = '%a, %d %b %Y %H:%M:%S GMT'
        t = time.strptime(lastMod, arpaFormat)
        t = (t[0] - 1,) + t[1:]  # one year before last modification
        beforeMod = time.strftime(arpaFormat, time.gmtime(time.mktime(t)))
        self.writeTest(
            f'Opening <code>{path}</code><br>'
            f'with If-Modified-Since: {beforeMod}')
        rsp = self.getDoc(path, {'If-Modified-Since': beforeMod})
        size = len(rsp.read())
        lastMod = rsp.getheader('Last-Modified', '')
        self.writeMsg(f'Last modified: {lastMod}')
        if rsp.status != 200:
            self.error(
                f'Expected status of 200, received {rsp.status} {rsp.reason}.')
            return
        if size != originalSize:
            self.error(
                f'Received: {rsp.status} {rsp.reason},'
                f' document size = {size}, expected size = {originalSize}.')
            return
        self.writeMsg(
            f'Received: {rsp.status} {rsp.reason},'
            f' document size = {size} (as expected).')
        self.writeTest(f'{self.__class__.__name__} passed.')
