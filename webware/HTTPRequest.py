"""HTTP requests"""

import cgi
import os
import sys
import traceback
from operator import itemgetter
from time import time
from http.cookies import SimpleCookie as Cookie

import HTTPResponse

from MiscUtils import NoDefault
from WebUtils import FieldStorage
from Request import Request

debug = False


class HTTPRequest(Request):
    """The base class for HTTP requests."""

    # region Initialization

    def __init__(self, requestDict=None):
        Request.__init__(self)
        self._stack = []
        if requestDict:
            # Dictionaries come in from interfaces like WSGI
            if requestDict['format'] != 'CGI':
                raise ValueError(
                    'Request dict for HTTPRequest must have CGI format')
            self._time = requestDict['time']
            self._environ = requestDict['environ']
            self._input = requestDict['input']
            self._requestID = requestDict['requestID']
            # Protect the loading of fields with an exception handler,
            # because bad headers sometimes can break the field storage
            # (see also https://bugs.python.org/issue27777).
            try:
                self._fields = FieldStorage.FieldStorage(
                    self._input, environ=self._environ,
                    keep_blank_values=True, strict_parsing=False)
            except Exception:
                self._fields = cgi.FieldStorage(keep_blank_values=True)
                traceback.print_exc(file=sys.stderr)
            self._cookies = Cookie()
            if 'HTTP_COOKIE' in self._environ:
                # If there are duplicate cookies, always use the first one
                # because it is the most relevant one according to RFC 2965
                # (workaround for https://bugs.python.org/issue1375011).
                # noinspection PyTypeChecker
                cookies = dict(cookie.split('=', 1) for cookie in reversed(
                    self._environ['HTTP_COOKIE'].split('; ')))
                # Protect the loading of cookies with an exception handler,
                # because MSIE cookies sometimes can break the cookie module.
                try:
                    self._cookies.load(cookies)
                except Exception:
                    traceback.print_exc(file=sys.stderr)
        else:
            # If there's no dictionary, we pretend we're a CGI script
            # and see what happens...
            self._time = time()
            self._environ = os.environ.copy()
            self._input = None
            self._fields = cgi.FieldStorage(keep_blank_values=True)
            self._cookies = Cookie()

        env = self._environ

        # Debugging
        if debug:
            with open('env.text', 'a') as f:
                f.write('>> env for request:\n')
                for key in sorted(env):
                    f.write(f'{key}: {env[key]!r}\n')
                f.write('\n')

        # Get servlet path and query string
        self._servletPath = env.get('SCRIPT_NAME', '')
        self._pathInfo = env.get('PATH_INFO', '')
        self._extraURLPath = ''  # will be determined later
        self._queryString = env.get('QUERY_STRING', '')
        if 'REQUEST_URI' in env:
            self._uri = env['REQUEST_URI']
            # correct servletPath if there was a redirection
            if not (self._uri + '/').startswith(self._servletPath + '/'):
                i = self._uri.find(self._pathInfo)
                self._servletPath = self._uri[:i] if i > 0 else ''
        else:
            # REQUEST_URI isn't actually part of the CGI standard and some
            # web servers like IIS don't set it (as of 8/22/2000).
            if 'SCRIPT_URL' in env:
                self._uri = env['SCRIPT_URL']
                # correct servletPath if there was a redirection
                if not (self._uri + '/').startswith(self._servletPath + '/'):
                    i = self._uri.find(self._pathInfo)
                    self._servletPath = self._uri[:i] if i > 0 else ''
            else:
                self._uri = self._servletPath + self._pathInfo
            if self._queryString:
                self._uri += '?' + self._queryString

        # We use the cgi module to get the fields,
        # but then change them into an ordinary dictionary of values:
        fieldStorage, fields = self._fields, {}
        try:
            # Avoid accessing fieldStorage as dict; that would be very slow
            # as it always iterates over all items to find a certain key.
            # Instead, iterate directly over the items of the internal list.
            fieldItems = fieldStorage.list
        except AttributeError:
            # This can happen if we do not have a a regular POST
            # from an HTML form, but, for example, an XML-RPC request.
            fieldItems = None
            if debug:
                print("Cannot get fieldStorage list.")
        if fieldItems:
            for item in fieldItems:
                if item.filename:
                    if debug:
                        print("Uploaded file found:", item.filename)
                    fields.setdefault(item.name, []).append(item)
                else:
                    fields.setdefault(item.name, []).append(item.value)
            for key, value in fields.items():
                if len(value) == 1:
                    fields[key] = value[0]
        self._fieldStorage, self._fields = fieldStorage, fields

        # We use Tim O'Malley's Cookie class to get the cookies,
        # but then change them into an ordinary dictionary of values
        self._cookies = dict(
            (key, self._cookies[key].value) for key in self._cookies)

        self._contextName = None
        self._serverSidePath = self._serverSideContextPath = None
        self._serverRootPath = ''
        self._sessionExpired = False

        self._pathInfo = self.pathInfo()

        if debug:
            print("Done setting up request, found fields:", ', '.join(fields))

    # endregion Initialization

    # region Protocol

    def protocol(self):
        """Return the name and version of the protocol."""
        return self._environ.get('SERVER_PROTOCOL', 'HTTP/1.0')

    # endregion Protocol

    # region Security

    def isSecure(self):
        """Check whether this is a HTTPS connection."""
        return self._environ.get('wsgi.url_scheme') == 'https'

    # endregion Security

    # region Transactions

    def responseClass(self):
        return HTTPResponse.HTTPResponse

    # endregion Transactions

    # region Values

    def value(self, name, default=NoDefault):
        """Return the value with the given name.

        Values are fields or cookies.
        Use this method when you're field/cookie agnostic.
        """
        if name in self._fields:
            return self._fields[name]
        return self.cookie(name, default)

    def hasValue(self, name):
        """Check whether there is a value with the given name."""
        return name in self._fields or name in self._cookies

    def extraURLPath(self):
        """Return additional path components in the URL.

        Only works if the Application.config setting "ExtraPathInfo"
        is set to true; otherwise you will get a page not found error.
        """
        return self._extraURLPath

    # endregion Values

    # region Fields

    def fieldStorage(self):
        return self._fieldStorage

    def field(self, name, default=NoDefault):
        if default is NoDefault:
            return self._fields[name]
        return self._fields.get(name, default)

    def hasField(self, name):
        return name in self._fields

    def fields(self):
        return self._fields

    def setField(self, name, value):
        self._fields[name] = value

    def delField(self, name):
        del self._fields[name]

    # endregion Fields

    # region Cookies

    def cookie(self, name, default=NoDefault):
        """Return the value of the specified cookie."""
        if default is NoDefault:
            return self._cookies[name]
        return self._cookies.get(name, default)

    def hasCookie(self, name):
        """Return whether a cookie with the given name exists."""
        return name in self._cookies

    def cookies(self):
        """Return a dict of all cookies the client sent with this request."""
        return self._cookies

    # endregion Cookies

    # region Variables passed by server

    def serverDictionary(self):
        """Return a dictionary with the data the web server gave us.

        This data includes HTTP_HOST and HTTP_USER_AGENT, for example.
        """
        return self._environ

    # endregion Variables passed by server

    # region Sessions

    def session(self):
        """Return the session associated with this request.

        The session is either as specified by sessionId() or newly created.
        This is a convenience for transaction.session()
        """
        return self._transaction.session()

    def isSessionExpired(self):
        """Return whether the request originally had an expired session ID.

        Only works if the Application.config setting "IgnoreInvalidSession"
        is set to true; otherwise you get a canned error page on an invalid
        session, so your servlet never gets processed.
        """
        return self._sessionExpired

    def setSessionExpired(self, sessionExpired):
        self._sessionExpired = sessionExpired

    # endregion Sessions

    # region  Remote info

    def remoteUser(self):
        """Always returns None since authentication is not yet supported.

        Take from CGI variable REMOTE_USER.
        """
        return self._environ['REMOTE_USER']

    def remoteAddress(self):
        """Return a string containing the IP address of the client."""
        return self._environ['REMOTE_ADDR']

    def remoteName(self):
        """Return the fully qualified name of the client that sent the request.

        Returns the IP address of the client if the name cannot be determined.
        """
        env = self._environ
        return env.get('REMOTE_NAME', env['REMOTE_ADDR'])

    def accept(self, which=None):
        """Return preferences as requested by the user agent.

        The accepted preferences are returned as a list of codes
        in the same order as they appeared in the header.
        In other words, the explicit weighting criteria are ignored.

        If you do not define otherwise which preferences you are
        interested in ('language', 'charset', 'encoding'), by default
        you will get the user preferences for the content types.
        """
        var = 'HTTP_ACCEPT'
        if which:
            var += '_' + which.upper()
        prefs = []
        for pref in self._environ.get(var, '').split(','):
            pref = pref.partition(';')[0].strip()
            prefs.append(pref)
        return prefs

    # endregion  Remote info

    # region Path

    def urlPath(self):
        """Get the URL path relative to the mount point, without query string.

        This is actually the same as pathInfo().

        For example, http://host/Webware/Context/Servlet?x=1
        yields '/Context/Servlet'.
        """
        return self._pathInfo

    def urlPathDir(self):
        """Same as urlPath, but only gives the directory.

        For example, http://host/Webware/Context/Servlet?x=1
        yields '/Context'.
        """
        return os.path.dirname(self.urlPath())

    def setURLPath(self, path):
        """Set the URL path of the request.

        There is rarely a need to do this. Proceed with caution.
        """
        self._pathInfo = path
        self._uri = self._servletPath + path
        if self._queryString:
            self._uri += '?' + self._queryString

    def serverSidePath(self, path=None):
        """Return the absolute server-side path of the request.

        If the optional path is passed in, then it is joined with the
        server side directory to form a path relative to the object.
        """
        if path:
            if path.startswith('/'):
                path = path[1:]
            return os.path.normpath(os.path.join(
                os.path.dirname(self._serverSidePath), path))
        return self._serverSidePath

    def serverSideContextPath(self, path=None):
        """Return the absolute server-side path of the context of this request.

        If the optional path is passed in, then it is joined with the server
        side context directory to form a path relative to the object.

        This directory could be different from the result of serverSidePath()
        if the request is in a subdirectory of the main context directory.
        """
        if path:
            if path.startswith('/'):
                path = path[1:]
            return os.path.normpath(os.path.join(
                self._serverSideContextPath, path))
        return self._serverSideContextPath

    def contextName(self):
        """Return the name of the context of this request.

        This isn't necessarily the same as the name of the directory
        containing the context.
        """
        return self._contextName

    def servletURI(self):
        """Return servlet URI without any query strings or extra path info."""
        p = self._pathInfo
        if not self._extraURLPath:
            if p.endswith('/'):
                p = p[:-1]
            return p
        i = p.rfind(self._extraURLPath)
        if i >= 0:
            p = p[:i]
        if p.endswith('/'):
            p = p[:-1]
        return p

    def uriWebwareRoot(self):
        """Return relative URL path of the Webware root location."""
        if not self._serverRootPath:
            self._serverRootPath = ''
            loc = self.urlPath()
            loc, curr = os.path.split(loc)
            while True:
                loc, curr = os.path.split(loc)
                if not curr:
                    break
                self._serverRootPath += "../"
        return self._serverRootPath

    def scheme(self):
        """Return the URI scheme of the request (http or https)."""
        return 'https' if self.isSecure() else 'http'

    def hostAndPort(self):
        """Return the hostname and port part from the URL of this request."""
        env = self._environ
        if 'HTTP_HOST' in env:
            return env['HTTP_HOST']
        if 'SERVER_NAME' in env:
            return env['SERVER_NAME']
        host = env.get('SERVER_ADDR', '') or 'localhost'
        port = env.get('SERVER_PORT', '')
        defaultPort = '443' if self.isSecure() else '80'
        if port and port != defaultPort:
            host += ':' + port
        return host

    def serverURL(self, canonical=False):
        """Return the full Internet path to this request.

        This is the URL that was actually received by the web server
        before any rewriting took place. If canonical is set to true,
        then the canonical hostname of the server is used if possible.

        The path is returned without any extra path info or query strings,
        i.e. http://www.my.own.host.com:8080/Webware/TestPage.py
        """
        if canonical and 'SCRIPT_URI' in self._environ:
            return self._environ['SCRIPT_URI']
        return f'{self.scheme()}://{self.hostAndPort()}{self.serverPath()}'

    def serverURLDir(self):
        """Return the directory of the URL in full Internet form.

        Same as serverURL, but removes the actual page.
        """
        fullURL = self.serverURL()
        if fullURL and not fullURL.endswith('/'):
            fullURL = fullURL[:fullURL.rfind('/') + 1]
        return fullURL

    def serverPath(self):
        """Return the web server URL path of this request.

        This is the URL that was actually received by the web server
        before any rewriting took place.

        Same as serverURL, but without scheme and host.
        """
        if 'SCRIPT_URL' in self._environ:
            return self._environ['SCRIPT_URL']
        return self._servletPath + (
            self._stack[0][1] if self._stack else self._pathInfo)

    def serverPathDir(self):
        """Return the directory of the web server URL path.

        Same as serverPath, but removes the actual page.
        """
        fullURL = self.serverPath()
        if fullURL and not fullURL.endswith('/'):
            fullURL = fullURL[:fullURL.rfind('/') + 1]
        return fullURL

    def siteRoot(self):
        """Return the relative URL path of the home location.

        This includes all URL path components necessary to get back home
        from the current location.

        Examples:
            ''
            '../'
            '../../'

        You can use this as a prefix to a URL that you know is based off
        the home location. Any time you are in a servlet that may have been
        forwarded to from another servlet at a different level, you should
        prefix your URL's with this. That is, if servlet "Foo/Bar" forwards
        to "Qux", then the qux servlet should use siteRoot() to construct all
        links to avoid broken links. This works properly because this method
        computes the path based on the _original_ servlet, not the location
        of the servlet that you have forwarded to.
        """
        url = self.originalURLPath()
        if url.startswith('/'):
            url = url[1:]
        contextName = self.contextName() + '/'
        if url.startswith(contextName):
            url = url[len(contextName):]
        numStepsBack = url.count('/')
        return '../' * numStepsBack

    def siteRootFromCurrentServlet(self):
        """Return relative URL path to home seen from the current servlet.

        This includes all URL path components necessary to get back home
        from the current servlet (not from the original request).

        Similar to siteRoot() but instead, it returns the site root
        relative to the _current_ servlet, not the _original_ servlet.
        """
        url = self.urlPath()
        if url.startswith('/'):
            url = url[1:]
        contextName = self.contextName() + '/'
        if url.startswith(contextName):
            url = url[len(contextName):]
        numStepsBackward = url.count('/')
        return '../' * numStepsBackward

    def servletPathFromSiteRoot(self):
        """Return the "servlet path" of this servlet relative to the siteRoot.

        In other words, everything after the name of the context (if present).
        If you append this to the result of self.siteRoot() you get back to
        the current servlet. This is useful for saving the path to the current
        servlet in a database, for example.
        """
        urlPath = self.urlPath()
        if urlPath.startswith('/'):
            urlPath = urlPath[1:]
        parts = urlPath.split('/')
        newParts = []
        for part in parts:
            if part == '..' and newParts:
                newParts.pop()
            elif part != '.':
                newParts.append(part)
        if newParts[:1] == [self.contextName()]:
            newParts[:1] = []
        return '/'.join(newParts)

    # endregion Path

    # region Special

    def scriptName(self):
        """Return the name of the WSGI script as it appears in the URL.

        Example: '/Webware'
        Does not reflect redirection by the web server.
        Equivalent to the CGI variable SCRIPT_NAME.
        """
        return self._environ.get('SCRIPT_NAME', '')

    def scriptFileName(self):
        """Return the filesystem path of the WSGI script.

        Equivalent to the CGI variable SCRIPT_FILENAME.
        """
        return self._environ.get('SCRIPT_FILENAME', '')

    def environ(self):
        """Get the environment for the request."""
        return self._environ

    def push(self, servlet, url=None):
        """Push servlet and URL path on a stack, setting a new URL."""
        self._stack.append((servlet, self.urlPath(), self._contextName,
                            self._serverSidePath, self._serverSideContextPath,
                            self._serverRootPath, self._extraURLPath))
        if url is not None:
            self.setURLPath(url)

    def pop(self):
        """Pop URL path and servlet from the stack, returning the servlet."""
        if self._stack:
            (servlet, url, self._contextName,
             self._serverSidePath, self._serverSideContextPath,
             self._serverRootPath, self._extraURLPath) = self._stack.pop()
            if url is not None:
                self.setURLPath(url)
            return servlet

    def servlet(self):
        """Get current servlet for this request."""
        return self._transaction.servlet()

    def originalServlet(self):
        """Get original servlet before any forwarding."""
        if self._stack:
            return self._stack[0][0]
        return self.servlet()

    def previousServlet(self):
        """Get the servlet that passed this request to us, if any."""
        if self._stack:
            return self._stack[-1][0]

    parent = previousServlet  # kept old name as synonym

    def previousServlets(self):
        """Get the list of all previous servlets."""
        return [s[0] for s in self._stack]

    parents = previousServlets  # kept old name as synonym

    def originalURLPath(self):
        """Get URL path of the original servlet before any forwarding."""
        if self._stack:
            return self._stack[0][1]
        return self.urlPath()

    def previousURLPath(self):
        """Get the previous URL path, if any."""
        if self._stack:
            return self._stack[-1][1]

    def previousURLPaths(self):
        """Get the list of all previous URL paths."""
        return [s[1] for s in self._stack]

    def originalURI(self):
        """Get URI of the original servlet before any forwarding."""
        if self._stack:
            return self._servletPath + self._stack[0][1]
        return self.uri()

    def previousURI(self):
        """Get the previous URI, if any."""
        if self._stack:
            return self._servletPath + self._stack[-1][1]

    def previousURIs(self):
        """Get the list of all previous URIs."""
        return [self._servletPath + s[1] for s in self._stack]

    def originalContextName(self):
        """Return the name of the original context before any forwarding."""
        if self._stack:
            return self._stack[0][2]
        return self._contextName

    def previousContextName(self):
        """Get the previous context name, if any."""
        if self._stack:
            return self._stack[-1][2]

    def previousContextNames(self):
        """Get the list of all previous context names."""
        return [s[2] for s in self._stack]

    def rawInput(self, rewind=False):
        """Get the raw input from the request.

        This gives you a file-like object for the data that was sent with
        the request (e.g., the body of a POST request, or the document
        uploaded in a PUT request).

        The file might not be rewound to the beginning if there was valid,
        form-encoded POST data. Pass rewind=True if you want to be sure
        you get the entire body of the request.
        """
        fs = self.fieldStorage()
        if fs is None:
            return None
        if rewind and fs.file:
            fs.file.seek(0)
        return fs.file

    def time(self):
        """Return the time that the request was received."""
        return self._time

    def requestID(self):
        """Return the request ID.

        The request ID is a serial number unique to this request
        (at least unique for one run of the Application).
        """
        return self._requestID

    # endregion Special

    # region Information

    def servletPath(self):
        """Return the base URL for the servlets, sans host.

        This is useful in cases when you are constructing URLs.
        See Testing/Main.py for an example use.

        Roughly equivalent to the CGI variable SCRIPT_NAME,
        but reflects redirection by the web server.
        """
        return self._servletPath

    def contextPath(self):
        """Return the portion of the URI that is the context of the request."""
        return self._serverSideContextPath

    def pathInfo(self):
        """Return any extra path information as sent by the client.

        This is anything after the servlet name but before the query string.
        Equivalent to the CGI variable PATH_INFO.
        """
        return self._pathInfo

    def pathTranslated(self):
        """Return extra path information translated as file system path.

        This is the same as pathInfo() but translated to the file system.
        Equivalent to the CGI variable PATH_TRANSLATED.
        """
        return self._environ.get('PATH_TRANSLATED', '')

    def queryString(self):
        """Return the query string portion of the URL for this request.

        Equivalent to the CGI variable QUERY_STRING.
        """
        return self._queryString

    def uri(self):
        """Return the URI for this request (everything after the host name).

        This is the URL that was actually received by the web server
        before any rewriting took place, including the query string.
        Equivalent to the CGI variable REQUEST_URI.
        """
        return self._uri

    def method(self):
        """Return the HTTP request method (in all uppercase).

        Typically from the set GET, POST, PUT, DELETE, OPTIONS and TRACE.
        """
        return self._environ['REQUEST_METHOD'].upper()

    def sessionId(self):
        """Return a string with the session ID specified by the client.

        Returns None if there is no session ID.
        """
        trans = self._transaction
        app = trans.application()
        sid = self.value(app.sessionName(trans), None)
        if app.setting('Debug')['Sessions']:
            print('>> sessionId: returning sid =', sid)
        return sid

    def setSessionId(self, sessionID, force=False):
        """Set the session ID.

        This needs to be called _before_ attempting to use the session.
        This would be useful if the session ID is being passed in through
        unusual means, for example via a field in an XML-RPC request.

        Pass in force=True if you want to force this session ID to be used
        even if the session doesn't exist. This would be useful in unusual
        circumstances where the client is responsible for creating the unique
        session ID rather than the server.
        Be sure to use only legal filename characters in the session ID --
        0-9, a-z, A-Z, _, -, and . are OK but everything else will be rejected,
        as will identifiers longer than 80 characters.
        (Without passing in force=True, a random session ID will be generated
        if that session ID isn't already present in the session store.)
        """
        # Modify the request so that it looks like a hashed version of the
        # given session ID was passed in
        trans = self._transaction
        app = trans.application()
        self.setField(app.sessionName(trans), sessionID)
        if force:
            # Force this session ID to exist, so that a random session ID
            # won't be created in case it's a new session.
            app.createSessionWithID(trans, sessionID)

    # endregion Information

    # region Inspection

    def info(self):
        """Return request info.

        Return a list of tuples where each tuple has a key/label (a string)
        and a value (any kind of object).

        Values are typically atomic values such as numbers and strings or
        another list of tuples in the same fashion. This is for debugging only.
        """
        info = [
            ('time', self._time),
            ('environ', self._environ),
            ('input', self._input),
            ('fields', self._fields),
            ('cookies', self._cookies)
        ]
        for method in _infoMethods:
            try:
                info.append((method.__name__, method(self)))
            except Exception:
                info.append((method.__name__, None))
        return info

    def htmlInfo(self):
        """Return a single HTML string that represents info().

        Useful for inspecting objects via web browsers.
        """
        return htmlInfo(self.info())

    _exceptionReportAttrNames = Request._exceptionReportAttrNames + [
        'uri', 'scriptName', 'servletPath', 'serverSidePath'
        'pathInfo', 'pathTranslated', 'queryString', 'method',
        'sessionId', 'previousURLPaths', 'fields', 'cookies', 'environ']

    # endregion Inspection


# region Info structure

_infoMethods = (
    HTTPRequest.scriptName,
    HTTPRequest.servletPath,
    HTTPRequest.contextPath,
    HTTPRequest.pathInfo,
    HTTPRequest.pathTranslated,
    HTTPRequest.queryString,
    HTTPRequest.uri,
    HTTPRequest.method,
    HTTPRequest.sessionId
)


def htmlInfo(info):
    """Return a single HTML string that represents the info structure.

    Useful for inspecting objects via web browsers.
    """
    res = ['<table>\n']
    for pair in info:
        value = pair[1]
        if hasattr(value, 'items') and (
                isinstance(value, dict) or hasattr(value, '__getitem__')):
            value = htmlInfo(_infoForDict(value))
        res.append(
            f'<tr style="vertical-align:top"><td>{pair[0]}</td>'
            f'<td>{value}&nbsp;</td></tr>\n')
    res.append('</table>\n')
    return ''.join(res)


def _infoForDict(d):
    """Return an "info" structure for any dictionary-like object."""
    return sorted(d.items, key=itemgetter(0))

# endregion Info structure
