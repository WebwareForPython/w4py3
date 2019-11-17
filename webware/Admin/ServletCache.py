import os
import time

from URLParser import ServletFactoryManager
from WebUtils.Funcs import htmlEncode
from .AdminSecurity import AdminSecurity


class ServletCache(AdminSecurity):
    """Display servlet cache.

    This servlet displays, in a readable form, the internal data
    structure of the cache of all servlet factories.

    This can be useful for debugging Webware problems and the
    information is interesting in general.
    """

    def title(self):
        return 'Servlet Cache'

    def writeContent(self):
        wr = self.writeln
        factories = [
            factory for factory in ServletFactoryManager._factories
            if factory._classCache]
        if not factories:
            wr('<h4>No caching servlet factories found.</h4>')
            wr('<p>Caching can be activated by setting'
               ' <code>CacheServletClasses = True</code>.</p>')
        if len(factories) > 1:
            factories.sort()
            wr('<h3>Servlet Factories:</h3>')
            wr('<table>')
            for factory in factories:
                name = factory.name()
                wr('<tr><td><a href="#{0}">{0}</a></td></tr>'.format(name))
            wr('</table>')
        hasField = self.request().hasField
        wr('<form action="ServletCache" method="post">')
        for factory in factories:
            name = factory.name()
            wr('<a id="{0}"></a><h4>{0}</h4>'.format(name))
            if hasField('flush_' + name):
                factory.flushCache()
                wr('<p style="color:green">'
                   'The servlet cache has been flushed. &nbsp; '
                   '<input type="submit" name="reload" value="Reload"></p>')
                continue
            wr(htCache(factory))
        wr('</form>')


def htCache(factory):
    """Output the cache of a servlet factory."""
    html = []
    wr = html.append
    cache = factory._classCache
    keys = sorted(cache)
    wr(f'<p>Uniqueness: {factory.uniqueness()}</p>')
    extensions = ', '.join(map(repr, factory.extensions()))
    wr(f'<p>Extensions: {extensions}</p>')
    name = factory.name()
    wr(f'<p>Unique paths in the servlet cache: <strong>{len(keys)}</strong>'
       f' &nbsp; <input type="submit" name="flush_{name}" value="Flush"></p>')
    wr('<p>Click any link to jump to the details for that path.</p>')
    wr('<h5>Filenames:</h5>')
    wr('<table class="NiceTable">')
    wr('<tr><th>File</th><th>Directory</th></tr>')
    paths = []
    for key in keys:
        head, tail = os.path.split(key)
        path = dict(dir=head, base=tail, full=key, id=id(key))
        paths.append(path)
    paths.sort(key=lambda p: (p['base'].lower(), p['dir'].lower()))
    for path in paths:
        wr('<tr><td><a href="#id{id}">{base}</a></td>'
           '<td>{dir}</td></tr>'.format(**path))
    wr('</table>')
    wr('<h5>Full paths:</h5>')
    wr('<table class="NiceTable">')
    wr('<tr><th>Servlet path</th></tr>')
    for key in keys:
        wr(f'<tr><td><a href="#{id(key)}">{key}</a></td></tr>')
    wr('</table>')
    wr('<h5>Details:</h5>')
    wr('<table class="NiceTable">')
    for path in paths:
        wr('<tr class="NoTable"><td colspan="2"><a id="id{id}"></a>'
           '<strong>{base}</strong> - {dir}</td></tr>'.format(**path))
        record = cache[path['full']].copy()
        record['path'] = path['full']
        record['instances'] = (
            'one servlet instance (threadsafe)'
            if path['full'] in factory._threadsafeServletCache else
            f'free reusable servlets: {len(factory._servletPool)}')
        wr(htRecord(record))
    wr('</table>')
    return '\n'.join(html)


def htRecord(record):
    html = []
    wr = html.append
    for key in sorted(record):
        htKey = htmlEncode(key)
        # determine the HTML for the value
        value = record[key]
        htValue = None
        # check for special cases where we want a custom display
        if hasattr(value, '__name__'):
            htValue = value.__name__
        if key == 'mtime':
            htValue = time.asctime(time.localtime(value))
            htValue = f'{htValue} ({value})'
        # the general case:
        if not htValue:
            htValue = htmlEncode(str(value))
        wr(f'<tr><th>{htKey}</th><td>{htValue}</td></tr>')
    return '\n'.join(html)
