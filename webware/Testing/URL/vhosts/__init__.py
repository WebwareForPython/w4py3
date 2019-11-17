from URLParser import URLParser


class VHostParser(URLParser):

    def parseHook(self, trans, requestPath, app, hook):
        host = trans.request().environ()['HTTP_HOST']
        hook.parse(trans, f'/{host}{requestPath}', app)


urlParserHook = VHostParser()
