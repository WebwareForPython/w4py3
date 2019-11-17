import sys

from importlib import reload

from .AdminSecurity import AdminSecurity


class AppControl(AdminSecurity):

    def writeContent(self):
        req = self.request()
        wr = self.writeln
        action = self.request().field("action", None)

        if action is None:
            wr('''<form action="AppControl" method="post">
<table>
<tr><td><input type="submit" name="action" value="Clear cache"></td>
<td>Clear the class and instance caches of each servlet factory.</td>
</tr><tr>
<td><input type="submit" name="action" value="Reload"></td>
<td>Reload the selected Python modules. Be careful!</td></tr>''')
            wr('<tr><td></td><td>')
            for n in sorted(sys.modules):
                m = sys.modules[n]
                if (not n.endswith('__init__') and not hasattr(m, '__path__')
                        and not hasattr(m, '__orig_file__')):
                    # show only the easily reloadable modules
                    wr(f'<input type="checkbox" name="reloads" value="{n}">'
                       f' {n}<br>')
            wr('</td></tr>\n</table>\n</form>')

        elif action == "Clear cache":
            from URLParser import ServletFactoryManager
            factories = [f for f in ServletFactoryManager._factories
                         if f._classCache]
            wr('<p>')
            for factory in factories:
                wr(f'Flushing cache of {factory.name()}...<br>')
                factory.flushCache()
            wr('</p>')
            wr('<p style="color:green">The caches of all factories'
               ' have been flushed.</p>')
            wr('<p>Click here to view the Servlet cache:'
               ' <a href="ServletCache">Servlet Cache</a></p>')

        elif action == "Reload":
            wr('<p>Reloading selected modules. Any existing classes'
               ' will continue to use the old module definitions,'
               ' as will any functions/variables imported using "from".'
               ' Use "Clear Cache" to clean out any servlets'
               ' in this condition.<p>')
            reloadNames = req.field("reloads", None)
            if not isinstance(reloadNames, list):
                reloadNames = [reloadNames]
            wr('<p>')
            for n in reloadNames:
                m = sys.modules.get(n)
                if m:
                    wr(f"Reloading {self.htmlEncode(str(m))}...<br>")
                    try:
                        reload(m)
                    except Exception as e:
                        wr('<span style="color:red">Could not reload, '
                           f'error was "{e}".</span><br>')
            wr('</p>')
            wr('<p style="color:green">The selected modules'
               ' have been reloaded.</p>')

        else:
            wr(f'<p>Cannot perform "{action}".</p>')
