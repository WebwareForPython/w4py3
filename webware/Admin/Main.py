import os
from time import time, localtime, gmtime, asctime

from .AdminSecurity import AdminSecurity


class Main(AdminSecurity):

    def title(self):
        return 'Admin'

    def writeContent(self):
        self.curTime = time()
        self.writeGeneralInfo()
        self.writeSignature()

    def writeGeneralInfo(self):
        app = self.application()
        info = (
            ('Webware Version', app.webwareVersionString()),
            ('Local Time', asctime(localtime(self.curTime))),
            ('Up Since', asctime(localtime(app.startTime()))),
            ('Num Requests', app.numRequests()),
            ('Working Dir', os.getcwd()),
            ('Active Sessions', len(app.sessions()))
        )
        self.writeln('''
<h2 style="text-align:center">Webware Administration Pages</h2>
<table style="margin-left:auto;margin-right:auto" class="NiceTable">
<tr class="TopHeading"><th colspan="2">Application Info</th></tr>''')
        for label, value in info:
            self.writeln(
                f'<tr><th style="text-align:left">{label}:</th>'
                f'<td>{value}</td></tr>')
        self.writeln('</table>')

    def writeSignature(self):
        self.writeln(f'''
<!--
begin-parse
{{
'Version': {self.application().webwareVersion()!r},
'LocalTime': {localtime(self.curTime)!r},
'GlobalTime': {gmtime(self.curTime)!r}
}}
end-parse
-->''')
