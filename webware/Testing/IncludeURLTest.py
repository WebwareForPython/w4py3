from Page import Page


class IncludeURLTest(Page):
    """Test includeURL redirection.

    This test will test out the callMethodOfServlet and includeURL
    redirection. The forward() method works similar to these but is
    not tested here. The following operations are performed:

    The form fields are displayed, as seen by this servlet.

    The request environment of this servlet is displayed.

    The writeStatus method on the servlet IncludeURLTest2 which is
    found in the Dir subdirectory under Testing is called.

    The title method is called on several other servlets to demonstrate
    calling methods on servlets in different areas relative to here.

    Finally, the top level page of this context is included with includeURL.

    A 'Test Complete' message is displayed at the very end.
    """

    def writeBody(self):
        self.writeln('<body style="margin:6pt;font-family:sans-serif">')
        fields = self.request().fields()
        name = self.__class__.__name__
        self.writeln(f'<h2>{name}</h2>')
        module = self.__module__
        self.writeln(f'<h3>class = <code>{name}</code>,'
                     f' module= <code>{module}</code></h3>')
        doc = self.__class__.__doc__.replace('\n\n', '</p><p>')
        self.writeln(f'<p>{doc}</p>')
        self.writeln('<h4>Number of fields in the request.fields():'
                     f' {len(fields)}</h4>')
        self.writeln('<ul>')
        enc = self.htmlEncode
        for k, v in fields.items():
            self.writeln(f'<li>{enc(k)} = {enc(v)}</li>')
        self.writeln('</ul>')
        self.writeStatus()
        self.cmos(
            '/Testing/Dir/IncludeURLTest2', 'writeStatus',
            "Expect to see the status written by IncludeURLTest2"
            " which is the same format as the above status,"
            " only relative to /Testing/Dir.")
        self.cmos(
            'Dir/IncludeURLTest2', 'serverSidePath',
            "This returns the serverSide Path of the"
            " Dir/IncludeURLTest2 servlet. Notice that there is"
            " no leading '/' which means this test is relative to"
            " the current directory.")
        self.cmos(
            '/Testing/', 'name',
            "This returns the name of the module at the top of"
            " the Testing context which is 'Main'.")
        self.cmos(
            '/Testing/Main', 'serverSidePath',
            "This returns the serverSidePath of the servlet"
            " accessed at the top of this context.")
        self.cmos(
            'Main', 'serverSidePath',
            "This returns the serverSidePath of the servlet"
            " accessed 'Main' and should be the same as the"
            " servlet accessed through the Testing context.")
        self.writeln('<h4>Including Dir/IncludeURLTest2:</h4>')
        self.write('<div style="margin-left:2em">')
        self.includeURL('Dir/IncludeURLTest2')
        self.write('</div>')
        self.writeln('<h4>Including the Main servlet of the'
                     f' {self.request().contextName()} context:</h4>')
        self.write('<div style="margin-left:2em">')
        self.includeURL('Main')
        self.write('</div>')
        self.writeln(f'<h4>{name} complete.</h4>')
        self.writeln('</body>')

    def writeStatus(self):
        name = self.__class__.__name__
        self.writeln(f'<h4>Request Status of <code>{name}</code>:</h4>')
        w = self.wkv
        req = self.request()
        env = req._environ
        self.writeln("<pre>")
        w('serverSidePath()', req.serverSidePath())
        w('scriptName()', req.scriptName())
        w('servletPath()', req.servletPath())
        w('contextName()', req.contextName())
        w('serverSideContextPath()', req.serverSideContextPath())
        w('extraURLPath()', req.extraURLPath())
        w('urlPath()', req.urlPath())
        w('previousURLPaths()', ', '.join(req.previousURLPaths()))
        w('Environment', '')
        w('REQUEST_URI', env.get('REQUEST_URI', ''))
        w('PATH_INFO', env.get('PATH_INFO', ''))
        w('SCRIPT_NAME', env.get('SCRIPT_NAME', ''))
        w('SCRIPT_FILENAME', env.get('SCRIPT_FILENAME', ''))
        self.writeln('</pre>')

    def wkv(self, k, v):
        self.writeln(f'{k}: {self.htmlEncode(v)}')

    def cmos(self, url, method, desc):
        self.writeln(
            '<p>Calling'
            f' <code>callMethodOfServlet(t, {url!r}, {method!r})</code>:</p>'
            f'<p>{desc}</p>')
        self.write('<div style="margin-left:2em">')
        ret = self.callMethodOfServlet(url, method)
        self.write('</div>')
        ret = 'nothing' if ret is None else f'<code>{ret}</code>'
        self.writeln(
            f'<p><code>callMethodOfServlet</code> returned {ret}.</p>')
