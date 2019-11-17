from .ExamplePage import ExamplePage


class RequestInformation(ExamplePage):
    """Request information demo."""

    def writeContent(self):
        self.writeln('<h3>Request Variables</h3>')
        request = self.request()
        self.writeln(
            '<p>The following table shows the values'
            ' for three important request variables.</p>')
        p = 'We added some cookies for you.'
        if not self.request().hasCookie('TestCookieName'):
            p += (' <a href="RequestInformation">Reload the page'
                  ' to see them.</a>')
        if not request.fields():
            p += (' <a href="RequestInformation?'
                  'answer=42&list=1&list=2&list=3&question=what">'
                  'You can also add some test fields.</a>')
        self.writeln(f'<p>{p}</p>')
        self.writeln('<table style="font-size:small;width:100%">')
        if request.fields():
            self.showDict('fields()', request.fields())
        self.showDict('environ()', request.environ())
        if request.cookies():
            self.showDict('cookies()', request.cookies())
        self.writeln('</table>')
        setCookie = self.response().setCookie
        setCookie('TestCookieName', 'CookieValue')
        setCookie('TestAnotherCookie', 'AnotherCookieValue')
        setCookie('TestExpire1', 'expires in 1 minute', expires='+1m')
        setCookie('TestExpire2', 'expires in 2 minute', expires='+2m')
        setCookie('TestExpire3', 'expires in 3 minute', expires='+3m')

    def showDict(self, name, d):
        self.writeln(
            '<tr style="vertical-align:top">'
            f'<td style="background-color:#ccf" colspan="2">{name}</td>'
            '</tr>')
        for key in sorted(d):
            html = self.htmlEncode(str(d[key])).replace('\n', '<br>').replace(
                ',', ',<wbr>').replace(';', ';<wbr>').replace(':/', ':<wbr>/')
            self.writeln(
                '<tr style="vertical-align:top;background-color:#eef">'
                f'<td>{key}</td><td>{html}</td></tr>')
