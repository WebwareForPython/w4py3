import datetime
import time

from SidebarPage import SidebarPage

cookieValues = [
    ('onclose', 'ONCLOSE'),
    ('expireNow', 'NOW'),
    ('expireNever', 'NEVER'),
    ('oneMinute', '+1m'),
    ('oneWeek', '+1w'),
    ('oneHourAndHalf', '+ 1h 30m'),
    ('timeIntTenSec', time.time() + 10),
    ('tupleOneYear', (time.localtime()[0] + 1,) + time.localtime()[1:]),
    ('dt1day', datetime.datetime.now() + datetime.timedelta(1)),
    ('dt2min', datetime.timedelta(minutes=2))
]

cookieIndex = 1


class SetCookie(SidebarPage):

    def cornerTitle(self):
        return 'Testing'

    def writeContent(self):
        global cookieIndex
        res = self.response()
        req = self.request()
        enc = self.htmlEncode
        self.writeln('<h4>The time right now is:</h4>')
        t = time.strftime('%a, %d-%b-%Y %H:%M:%S GMT', time.gmtime())
        self.writeln(f'<p>{t}</p>')
        self.writeln('<h2>Cookies received:</h2>\n')
        self.writeln('<ul>')
        for name, value in req.cookies().items():
            self.writeln(f'<li>{name!r} = {enc(value)}</li>')
        self.writeln('</ul>')
        for name, expire in cookieValues:
            res.setCookie(name, f'Value #{cookieIndex}', expires=expire)
            cookieIndex += 1
        self.writeln('<h2>Cookies being sent:</h2>\n')
        self.writeln('<dl>')
        for name, cookie in res.cookies().items():
            self.writeln(f'<dt>{name!r} sends:</dt>')
            self.writeln(f'<dd>{enc(cookie.headerValue())}</dd>')
        self.writeln('</dl>')
