from .AdminSecurity import AdminSecurity


class PlugIns(AdminSecurity):

    def writeContent(self):
        wr = self.writeln
        plugIns = self.application().plugIns()
        if plugIns:
            wr('<h4 style="text-align:center">'
               'The following Plug-ins were found:</h4>')
            wr('<table  class="NiceTable"'
               ' style="margin-left:auto;margin-right:auto">')
            wr('<tr class="TopHeading"><th colspan="3">Plug-ins</th></tr>')
            wr('<tr class="SubHeading">'
               '<th>Name</th><th>Version</th><th>Directory</th></tr>')
            for plugIn in plugIns.values():
                name, path = plugIn.name(), plugIn.path()
                ver = plugIn.properties()['versionString']
                wr(f'<tr><td>{name}</td>'
                   f'<td style="text-align:center">{ver}</td>'
                   f'<td>{path}</td></tr>')
            wr('</table>')
        else:
            wr('<h4 style="text-align:center">No Plug-ins found.</h4>')
