# pylint: disable=invalid-name

from Page import Page
from WebUtils.Funcs import htmlEncode as enc


class Inspector(Page):

    def writeContent(self):
        req = self.request()
        self.write('Path:<br>\n')
        self.write(f'<code>{enc(req.extraURLPath())}</code><p>\n')
        self.write('Variables:<br>\n')
        self.write('<table>')
        for name in sorted(req.fields()):
            self.write(
                f'<tr><td style="text-align:right">{enc(name)}:</td>'
                f'<td>{enc(req.field(name))}</td></tr>\n')
        self.write('</table><p>\n')
        self.write('Server-side path:<br>\n')
        self.write(f'<code>{enc(req.serverSidePath())}</code><p>\n')
