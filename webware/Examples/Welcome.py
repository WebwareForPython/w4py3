from .ExamplePage import ExamplePage


class Welcome(ExamplePage):

    def writeContent(self):
        wr = self.writeln
        version = self.application().webwareVersionString()
        wr(f'<h2>Welcome to Webware for Python {version}!</h2>')
        path = self.request().servletPath()
        wr(f'''
        <p>Along the side of this page you will see various links
        that will take you to:</p>
        <ul>
            <li>The different Webware examples.</li>
            <li>The source code of the current example.</li>
            <li>Whatever contexts have been configured.
                Each context represents a distinct set of web pages,
                usually given a descriptive name.</li>
            <li>External sites, such as the Webware home page.</li>
        </ul>
        <p>The <a href="{path}/Admin/">Admin</a> context is particularly
        interesting because it takes you to the administrative pages
        for the Webware application where you can review logs,
        configuration, plug-ins, etc.</p>
        ''')
        req = self.request()
        extraURLPath = req.extraURLPath()
        if extraURLPath and extraURLPath != '/':
            wr('''
            <p><strong>Note:</strong>
            extraURLPath information was found on the URL,
            and a servlet was not found to process it.
            Processing has been delegated to this servlet.</p>
            ''')
            wr('<ul>')
            wr(f'<li>serverSidePath: <code>{req.serverSidePath()}</code></li>')
            wr(f'<li>extraURLPath: <code>{extraURLPath}</code></li>')
            wr('</ul>')
