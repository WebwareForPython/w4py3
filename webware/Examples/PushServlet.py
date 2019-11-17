from time import sleep

from Page import Page


class PushServlet(Page):
    """Pushing Content Demo.

    This is a test servlet for the buffered output streams of the application.

    Server push is a simple way of sending file updates to a browser.
    It is not true streaming, though it can feel a lot like it when done well.

    The browser needs to support "multipart/x-mixed-replace" for this to work.
    Some browsers like MSIE do not support this, and others like Chrome have
    restricted it to images or dropped support for this feature.

    The WSGI server must also support this.

    This demo has been confirmed to work with Firefox 68 and waitress 1.3.
    """

    _boundary = ("if-you-see-this-your-browser-then"
                 "-it-does-not-support-multipart/x-mixed-replace")

    def respond(self, transaction):
        response = self.response()
        # this isn't necessary, but it's here as an example:
        response.streamOut().setAutoCommit()
        # send the initial header:
        self.initialHeader()
        self.sendBoundary()
        response.flush()
        # push new content 4 times:
        for i in range(4):
            self.pushHTML(i)
            self.sendBoundary()
            # send the currently buffered output now:
            response.flush()
            sleep(5 if i else 15)

    def initialHeader(self):
        setHeader = self.response().setHeader
        setHeader("Content-Type",
                  "multipart/x-mixed-replace; boundary=" + self._boundary)
        setHeader("X-Accel-Buffering", "no")

    def sendBoundary(self):
        self.write('--' + self._boundary + '\r\n')

    def pushHTML(self, count):
        self.write("Content-Type: text/html\r\n\r\n")
        wr = self.writeln
        wr('<html><body style="margin:8pt;"><div style='
           '"background-color:#eef;padding:8pt 16pt;border:2px solid blue">')
        wr('<h1>Pushing Content Demo</h1>')
        if count:
            wr('<h3>This page has been replaced'
               f' <strong style="color:#339">{count:d}</strong>'
               f" time{'' if count ==1 else 's'}.</h3>")
            if count == 3:
                wr('<p>Stopped pushing contents.</p>')
            else:
                wr('<p>Next content will be pushed'
                   ' <strong>in 5</strong> seconds.</p>')
        else:
            wr('<p>This servlet will try to replace the content'
               ' <strong>in 15 seconds</strong>.</p>')
        if not count or count == 3:
            wr('<h4>Note:</h4>')
            if count == 3:
                wr("<p>If you didn't get output for the last 30 seconds, "
                   'pushing contents is not supported.</p>')
            wr('<p>The browser must support the <code>x-mixed-replace</code>'
               ' content type. You should try with Firefox first.</p>')
        wr('</div></body></html>')
