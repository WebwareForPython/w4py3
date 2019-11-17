from Page import Page


class DebugPage(Page):

    def state(self):
        envVars = ('PATH_INFO', 'REQUEST_URI', 'SCRIPT_NAME')
        reqVars = (
            'urlPath', 'previousURLPaths',
            'scriptName', 'servletPath', 'contextName',
            'serverPath', 'serverSidePath', 'serverSideContextPath',
            'extraURLPath')
        req = self.request()
        env = req._environ
        s = []
        for key in envVars:
            value = env.get(key, "* not set *")
            s.append(f"  * env[{key!r}] = {value}")
        for key in reqVars:
            value = getattr(req, key)()
            s.append(f"  * req.{key}() = {value}")
        return '\n'.join(s)

    def writeContent(self):
        self.writeln(f'<h2><code>{self.__class__.__name__}</code></h2>')
        self.writeln(f'<pre>{self.state()}</pre>')
