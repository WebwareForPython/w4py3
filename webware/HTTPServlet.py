"""HTTP servlets"""

from time import gmtime, strftime

from Servlet import Servlet


class HTTPServlet(Servlet):
    """A HTTP servlet.

    HTTPServlet implements the respond() method to invoke methods such as
    respondToGet() and respondToPut() depending on the type of HTTP request.
    Example HTTP request methods are GET, POST, HEAD, etc.
    Subclasses implement HTTP method FOO in the Python method respondToFoo.
    Unsupported methods return a "501 Not Implemented" status.

    Note that HTTPServlet inherits awake() and respond() methods from
    Servlet and that subclasses may make use of these.

    See also: Servlet
    """

    # region Init

    def __init__(self):
        Servlet.__init__(self)
        self._methodForRequestType = {}  # a cache; see respond()

    # endregion Init

    # region Transactions

    def respond(self, transaction):
        """Respond to a request.

        Invokes the appropriate respondToSomething() method depending on the
        type of request (e.g., GET, POST, PUT, ...).
        """
        request = transaction.request()
        httpMethodName = request.method()
        # For GET and HEAD, handle the HTTP If-Modified-Since header:
        # If the object's last modified time equals this header, we're done.
        if httpMethodName in ('GET', 'HEAD'):
            lastMod = self.lastModified(transaction)
            if lastMod:
                lastMod = strftime(
                    '%a, %d %b %Y %H:%M:%S GMT', gmtime(lastMod))
                response = transaction.response()
                response.setHeader('Last-Modified', lastMod)
                envGet = request.environ().get
                ims = envGet('HTTP_IF_MODIFIED_SINCE') or envGet(
                    'IF_MODIFIED_SINCE')
                if ims and ims.partition(';')[0] == lastMod:
                    response.delHeader('Content-Type')
                    response.setStatus(304, 'Not Modified')
                    return
        method = self._methodForRequestType.get(httpMethodName)
        if not method:
            methodName = 'respondTo' + httpMethodName.capitalize()
            method = getattr(self, methodName, self.notImplemented)
            self._methodForRequestType[httpMethodName] = method
        method(transaction)

    @staticmethod
    def notImplemented(trans):
        trans.response().setStatus(501, 'Not Implemented')

    @staticmethod
    def lastModified(_trans):
        """Get time of last modification.

        Return this object's Last-Modified time (as a float),
        or None (meaning don't know or not applicable).
        """
        return None

    def respondToHead(self, trans):
        """Respond to a HEAD request.

        A correct but inefficient implementation.
        """
        res = trans.response()
        w = res.write
        res.write = lambda *args: None
        self.respondToGet(trans)  # pylint: disable=no-member
        res.write = w

    # endregion Transactions
