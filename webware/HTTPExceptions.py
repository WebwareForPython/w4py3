"""HTTP exceptions.

HTTPExceptions are for situations that are predicted by the HTTP spec.
Where the ``200 OK`` response is typical, a ``404 Not Found``
or ``301 Moved Temporarily`` response is not entirely unexpected.

`Application` catches all `HTTPException` exceptions (and subclasses of
HTTPException), and instead of being errors these are translated into
responses. In various places these can also be caught and changed, for instance
an `HTTPAuthenticationRequired` could be turned into a normal login page.
"""

from WebUtils.Funcs import htmlEncode


class HTTPException(Exception):
    """HTTPException template class.

    Subclasses must define these variables (usually as class variables):

    `_code`:
        a tuple of the integer error code, and the short
        description that goes with it (like ``(200, "OK")``)
    `_description`:
        the long-winded description, to be presented
        in the response page. Or you can override description()
        if you want something more context-sensitive.
    """

    def __str__(self):
        return f'{self.code()} {self.codeMessage()}'

    # region Error codes

    _description = 'An error occurred'

    def code(self):
        """The integer code."""
        return self._code[0]  # pylint: disable=no-member

    def codeMessage(self):
        """The message (like ``Not Found``) that goes with the code."""
        return self._code[1]  # pylint: disable=no-member

    # endregion Error codes

    # region HTML Description

    def html(self):
        """The error page.

        The HTML page that should be sent with the error,
        usually a description of the problem.
        """
        page = '''
<html><head><title>{code} {title}</title></head>
<body>
<h1>{htTitle}</h1>
{body}
</body></html>'''
        return page.format(
            htTitle=self.htTitle(), title=self.title(),
            body=self.htBody(), code=self.code())

    def title(self):
        """The title used in the HTML page."""
        return self.codeMessage()

    def htTitle(self):
        """The title, but it may include HTML markup (like italics)."""
        return self.title()

    def htBody(self):
        """The HTML body of the page."""
        body = self.htDescription()
        if self.args:  # pylint: disable=using-constant-test
            # pylint: disable=not-an-iterable
            body += ''.join(
                '<p>{}</p>\n'.format(htmlEncode(str(p)) for p in self.args))
        return body

    def description(self):
        """Error description.

        Possibly a plain text version of the error description,
        though usually just identical to `htDescription`.
        """
        return self._description

    def htDescription(self):
        """HTML error description.

        The HTML description of the error, for presentation
        to the browser user.
        """
        return self.description()

    # endregion HTML Description

    # region Misc

    def headers(self):
        """Get headers.

        Additional headers that should be sent with the
        response, not including the Status header. For instance,
        the redirect exception adds a Location header.
        """
        return {}

    def setTransaction(self, trans):
        """Set transaction.

        When the exception is caught by `Application`, it tells
        the exception what the transaction is. This way you
        can resolve relative paths, or otherwise act in a manner
        sensitive of the context of the error.
        """
        self._transaction = trans

    # endregion Misc


class HTTPMovedPermanently(HTTPException):
    """HTTPException "moved permanently" subclass.

    When a resource is permanently moved. The browser may remember this
    relocation, and later requests may skip requesting the original
    resource altogether.
    """
    _code = 301, 'Moved Permanently'

    def __init__(self, location=None, webwareLocation=None):
        """Set destination.

        HTTPMovedPermanently needs a destination that you it should be
        directed to -- you can pass `location` *or* `webwareLocation` --
        if you pass `webwareLocation` it will be relative to the Webware
        root location (the mount point of the WSGI application).
        """
        self._location = location
        self._webwareLocation = webwareLocation
        super().__init__()

    def location(self):
        """The location that we will be redirecting to."""
        if self._webwareLocation:
            location = self._transaction.request().servletPath()
            if not self._webwareLocation.startswith('/'):
                location += '/'
            location += self._webwareLocation
        else:
            location = self._location
        return location

    def headers(self):
        """We include a Location header."""
        return {'Location': self.location()}

    def description(self):
        return (
            'The resource you are accessing has been moved to'
            ' <a href="{0}">{0}</a>'.format(htmlEncode(self.location())))


class HTTPTemporaryRedirect(HTTPMovedPermanently):
    """HTTPException "temporary redirect" subclass.

    Like HTTPMovedPermanently, except the redirect is only valid for this
    request. Internally identical to HTTPMovedPermanently, except with a
    different response code. Browsers will check the server for each request
    to see where it's redirected to.
    """
    _code = 307, 'Temporary Redirect'


# This is what people mean most often:
HTTPRedirect = HTTPTemporaryRedirect


class HTTPBadRequest(HTTPException):
    """HTTPException "bad request" subclass.

    When the browser sends an invalid request.
    """
    _code = 400, 'Bad Request'


class HTTPAuthenticationRequired(HTTPException):
    """HTTPException "authentication required" subclass.

    HTTPAuthenticationRequired will usually cause the browser to open up an
    HTTP login box, and after getting login information from the user, the
    browser will resubmit the request. However, this should also trigger
    login pages in properly set up environments (though much code will not
    work this way).

    Browsers will usually not send authentication information unless they
    receive this response, even when other pages on the site have given 401
    responses before. So when using this authentication every request will
    usually be doubled, once without authentication, once with.
    """
    _code = 401, 'Authentication Required'
    _description = "You must log in to access this resource"

    def __init__(self, realm=None):
        if not realm:
            realm = 'Password required'
        if '"' in realm:
            raise ValueError('Realm must not contain quotation marks')
        self._realm = realm
        super().__init__()

    def headers(self):
        return {'WWW-Authenticate': f'Basic realm="{self._realm}"'}


# This is for wording mistakes:
HTTPAuthorizationRequired = HTTPAuthenticationRequired


class HTTPSessionExpired(HTTPException):
    """HTTPException "session expired" subclass.

    This is the same as HTTPAuthenticationRequired, but should be used
    in the situation when a session has expired.
    """
    _code = 401, 'Session Expired'
    _description = 'Your login session has expired - please log in again'


class HTTPForbidden(HTTPException):
    """HTTPException "forbidden" subclass.

    When access is not allowed to this resource. If the user is anonymous,
    and must be authenticated, then HTTPAuthenticationRequired is a preferable
    exception. If the user should not be able to get to this resource (at
    least through the path they did), or is authenticated and still doesn't
    have access, or no one is allowed to view this, then HTTPForbidden would
    be the proper response.
    """
    _code = 403, 'Forbidden'
    _description = "You are not authorized to access this resource"


class HTTPNotFound(HTTPException):
    """HTTPException "not found" subclass.

    When the requested resource does not exist. To be more secretive,
    it is okay to return a 404 if access to the resource is not permitted
    (you are not required to use HTTPForbidden, though it makes it more
    clear why access was disallowed).
    """
    _code = 404, 'Not Found'
    _description = 'The resource you were trying to access was not found'

    def html(self):
        trans = self._transaction
        page = trans.application()._error404
        if page:
            uri = trans.request().uri()
            return page.format(htmlEncode(uri))
        return HTTPException.html(self)


class HTTPMethodNotAllowed(HTTPException):
    """HTTPException "method not allowed" subclass.

    When a method (like GET, PROPFIND, POST, etc) is not allowed
    on this resource (usually because it does not make sense, not
    because it is not permitted). Mostly for WebDAV.
    """
    _code = 405, 'Method Not Allowed'
    _description = 'The method is not supported on this resource'


class HTTPRequestTimeout(HTTPException):
    """HTTPException "request timeout" subclass.

    The client did not produce a request within the time that the
    server was prepared to wait. The client may repeat the request
    without modifications at any later time.
    """
    _code = 408, 'Request Timeout'


class HTTPConflict(HTTPException):
    """HTTPException "conflict" subclass.

    When there's a locking conflict on this resource (in response to
    something like a PUT, not for most other conflicts). Mostly for WebDAV.
    """
    _code = 409, 'Conflict'


class HTTPUnsupportedMediaType(HTTPException):
    """HTTPException "unsupported media type" subclass.

    The server is refusing to service the request because the entity
    of the request is in a format not supported by the requested resource
    for the requested method.
    """
    _code = 415, 'Unsupported Media Type'


class HTTPPreconditionFailed(HTTPException):
    """HTTPException "Precondition Failed" subclass.

    During compound, atomic operations, when a precondition for an early
    operation fail, then later operations in will fail with this code.
    Mostly for WebDAV.
    """
    _code = 412, 'Precondition Failed'


class HTTPServerError(HTTPException):
    """HTTPException "Server Error" subclass.

    The server encountered an unexpected condition which prevented it
    from fulfilling the request.
    """
    _code = 500, 'Server Error'


class HTTPNotImplemented(HTTPException):
    """HTTPException "not implemented" subclass.

    When methods (like GET, POST, PUT, PROPFIND, etc) are not
    implemented for this resource.
    """
    _code = 501, "Not Implemented"
    _description = (
        "The method given is not yet implemented by this application")


class HTTPServiceUnavailable(HTTPException):
    """HTTPException "service unavailable" subclass.

    The server is currently unable to handle the request due to a temporary
    overloading or maintenance of the server. The implication is that this
    is a temporary condition which will be alleviated after some delay.
    """
    _code = 503, "Service Unavailable"
    _description = "The server is currently unable to handle the request"


class HTTPInsufficientStorage(HTTPException):
    """HTTPException "insufficient storage" subclass.

    When there is not sufficient storage, usually in response to a PUT when
    there isn't enough disk space. Mostly for WebDAV.
    """
    _code = 507, 'Insufficient Storage'
    _description = (
        'There was not enough storage space on the server'
        ' to complete your request')
