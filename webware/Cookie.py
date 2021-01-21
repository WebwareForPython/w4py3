import http.cookies as CookieEngine

from MiscUtils.Funcs import positiveId


class Cookie:
    """Delicious cookies.

    Cookie is used to create cookies that have additional attributes
    beyond their value.

    Note that web browsers don't typically send any information with
    the cookie other than its value. Therefore `HTTPRequest.cookie`
    simply returns a value such as an integer or a string.

    When the server sends cookies back to the browser, it can send a cookie
    that simply has a value, or the cookie can be accompanied by various
    attributes (domain, path, max-age, ...) as described in `RFC 2109`_.
    Therefore, in `HTTPResponse`, `setCookie` can take either an instance of
    the `Cookie` class, as defined in this module, or a value.

    Note that `Cookie` values get pickled (see the `pickle` module), so
    you can set and get cookies that are integers, lists, dictionaries, etc.

    .. _`RFC 2109`: ftp://ftp.isi.edu/in-notes/rfc2109.txt
    """

    # Future
    #
    # * This class should provide error checking in the setFoo()
    #   methods. Or maybe our internal Cookie implementation
    #   already does that?
    # * This implementation is probably not as efficient as it
    #   should be, [a] it works and [b] the interface is stable.
    #   We can optimize later.

    # region Init

    def __init__(self, name, value):
        """Create a cookie.

        Properties other than `name` and `value` are set with methods.
        """
        self._cookies = CookieEngine.SimpleCookie()
        self._name = name
        self._value = value
        self._cookies[name] = value
        self._cookie = self._cookies[name]

    def __repr__(self):
        return ('{}(id=0x{:x}, name={!r}, domain={!r},'
                ' path={!r}, value={!r}, expires={!r}, maxAge={!r}').format(
                    self.__class__.__name__, positiveId(self),
                    self.name(), self.domain(),
                    self.path(), self.value(), self.expires(), self.maxAge())

    # endregion Init

    # region Accessors

    def comment(self):
        return self._cookie['comment']

    def domain(self):
        return self._cookie['domain']

    def expires(self):
        return self._cookie['expires']

    def maxAge(self):
        return self._cookie['max-age']

    def name(self):
        return self._name

    def path(self):
        return self._cookie['path']

    def isSecure(self):
        return self._cookie['secure']

    def httpOnly(self):
        return self._cookie['httponly']

    def sameSite(self):
        try:
            return self._cookie['samesite']
        except KeyError:  # Python < 3.8
            return ''

    def value(self):
        return self._value

    def version(self):
        return self._cookie['version']

    # endregion Accessors

    # region Setters

    def setComment(self, comment):
        self._cookie['comment'] = comment

    def setDomain(self, domain):
        self._cookie['domain'] = domain

    def setExpires(self, expires):
        self._cookie['expires'] = expires

    def setMaxAge(self, maxAge):
        self._cookie['max-age'] = maxAge

    def setPath(self, path):
        self._cookie['path'] = path

    def setSecure(self, secure=True):
        self._cookie['secure'] = secure

    def setHttpOnly(self, httpOnly=True):
        self._cookie['httponly'] = httpOnly

    def setSameSite(self, sameSite='Strict'):
        try:
            self._cookie['samesite'] = sameSite
        except CookieEngine.CookieError:  # Python < 3.8
            pass

    def setValue(self, value):
        self._value = value
        self._cookies[self._name] = value

    def setVersion(self, version):
        self._cookie['version'] = version

    # endregion Setters

    # region Misc

    def delete(self):
        """Delete a cookie.

        When sent, this should delete the cookie from the user's
        browser, by making it empty, expiring it in the past,
        and setting its max-age to 0. One of these will delete
        the cookie for any browser (which one actually works
        depends on the browser).
        """
        self._value = ''
        self._cookie['expires'] = "Mon, 01-Jan-1900 00:00:00 GMT"
        self._cookie['max-age'] = 0

    def headerValue(self):
        """Return header value.

        Returns a string with the value that should be used
        in the HTTP headers.
        """
        values = list(self._cookies.values())
        if len(values) != 1:
            raise ValueError('Invalid cookie')
        return values[0].OutputString()

    # endregion Misc
