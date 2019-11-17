from HTTPServlet import HTTPServlet


class index(HTTPServlet):

    def respond(self, transaction):
        extraPath = transaction.request().extraURLPath()
        path = transaction.request().urlPath()
        if extraPath and path.endswith(extraPath):
            path = path[:-len(extraPath)]
        if not path.endswith('Welcome'):
            path = path.rpartition('/')[0] + '/Welcome' + extraPath
            # redirection via the server:
            transaction.application().forward(transaction, path)
            # redirection via the client:
            # trans.response().sendRedirect(path)
