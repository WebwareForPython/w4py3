"""PickleRPC.py

PickleRPC provides a Server object for connection to Pickle-RPC servers
for the purpose of making requests and receiving the responses.

    >>> from MiscUtils.PickleRPC import Server
    >>> server = Server('http://localhost:8080/Examples/PickleRPCExample')
    >>> server.multiply(10,20)
    200
    >>> server.add(10,20)
    30

See also: Server, PickleRPCServlet, Examples.PickleRPCExample

UNDER THE HOOD

Requests look like this::

    {
        'version':    1,  # default
        'action':     'call',  # default
        'methodName': 'NAME',
        'args':       (A, B, ...),  # default = (,)
        'keywords':   {'A': A, 'B': B, ...}  # default = {}
    }

Only 'methodName' is required since that is the only key without a
default value.

Responses look like this::

    {
        'timeReceived': N,
        'timeReponded': M,
        'value': V,
        'exception': E,
        'requestError': E,
    }

'timeReceived' is the time the initial request was received.
'timeResponded' is the time at which the response was finished, as
close to transmission as possible. The times are expressed as
number of seconds since the Epoch, e.g., ``time.time()``.

Value is whatever the method happened to return.

Exception may be 'occurred' to indicate that an exception
occurred, the specific exception, such as "KeyError: foo" or the
entire traceback (as a string), at the discretion of the server.
It will always be a non-empty string if it is present.

RequestError is an exception such as "Missing method
in request." (with no traceback) that indicates a problem with the
actual request received by the Pickle-RPC server.

Value, exception and requestError are all exclusive to each other.

SECURITY

Pickle RPC uses the SafeUnpickler class (in this module) to
prevent unpickling of unauthorized classes.  By default, it
doesn't allow _any_ classes to be unpickled.  You can override
`allowedGlobals()` or `findGlobal()` in a subclass as needed to
allow specific class instances to be unpickled.

Note that both `Transport` in this package and `PickleRPCServlet` in
the Webware main package are derived from `SafeUnpickler`.

CREDIT

The implementation of this module was taken directly from Python's
xmlrpclib and then transformed from XML-orientation to Pickle-orientation.

The zlib compression was adapted from code by Skip Montanaro that I found
here: http://manatee.mojam.com/~skip/python/
"""

__version__ = 1  # PickleRPC protocol version (not the pickle protocol used)

import zlib

from pickle import dumps, Unpickler, UnpicklingError
from io import StringIO
from xmlrpc.client import ProtocolError as _PE


class Error(Exception):
    """The abstract exception/error class for all PickleRPC errors."""


class ResponseError(Error):
    """Unhandled exceptions raised when the server was computing a response.

    These will indicate errors such as:
      * exception in the actual target method on the server
      * malformed responses
      * non "200 OK" status code responses
    """


class ProtocolError(ResponseError, _PE):
    """RPC protocol error."""


class RequestError(Error):
    """Errors originally raised by the server caused by malformed requests."""


class InvalidContentTypeError(ResponseError):
    """Invalid content type error."""

    def __init__(self, headers, content):
        ResponseError.__init__(self)
        self.headers = headers
        self.content = content

    def __repr__(self):
        content = self.content
        return (f'{self.__class__.__name__}:'
                ' Content type is not text/x-python-pickled-dict\n'
                f' headers = {self.headers}\ncontent =\n{content}')

    __str__ = __repr__


class SafeUnpickler:
    """Safe unpickler.

    For security reasons, we don't want to allow just anyone to unpickle
    anything.  That can cause arbitrary code to be executed.
    So this SafeUnpickler base class is used to control what can be unpickled.
    By default it doesn't let you unpickle any class instances at all,
    but you can create subclass that overrides allowedGlobals().

    Note that the PickleRPCServlet class in the Webware package is derived from
    this class and uses its load() and loads() methods to do all unpickling.
    """

    def allowedGlobals(self):
        """Allowed class names.

        Must return a list of (moduleName, klassName) tuples for all
        classes that you want to allow to be unpickled.

        Example::

            return [('datetime', 'date')]

        Allows datetime.date instances to be unpickled.
        """
        return []

    def findGlobal(self, module, klass):
        """Find class name."""
        if (module, klass) not in self.allowedGlobals():
            raise UnpicklingError(
                "For security reasons, you can\'t unpickle"
                f' objects from module {module} with type {klass}.')
        g = {}
        exec(f'from {module} import {klass} as theClass', g)
        return g['theClass']

    def load(self, file):
        """Unpickle a file."""
        safeUnpickler = Unpickler(file)
        safeUnpickler.find_global = self.findGlobal
        return safeUnpickler.load()

    def loads(self, s):
        """Unpickle a string."""
        return self.load(StringIO(s))


class Server:
    """uri [,options] -> a logical connection to an XML-RPC server

    uri is the connection point on the server, given as
    scheme://host/target.

    The standard implementation always supports the "http" scheme.
    If SSL socket support is available, it also supports "https".

    If the target part and the slash preceding it are both omitted,
    "/PickleRPC" is assumed.

    See the module doc string for more information.
    """

    def __init__(self, uri, transport=None, verbose=False, binary=True,
                 compressRequest=True, acceptCompressedResponse=True):
        """Establish a "logical" server connection."""
        # get the url
        import urllib.parse
        import urllib.error
        type_, uri = urllib.parse.splittype(uri)
        if type_ not in ('http', 'https'):
            raise IOError('unsupported Pickle-RPC protocol')
        self._host, self._handler = urllib.parse.splithost(uri)
        if not self._handler:
            self._handler = '/PickleRPC'

        if transport is None:
            transport = (SafeTransport if type_ == 'https' else Transport)()
        self._transport = transport

        self._verbose = verbose
        self._binary = binary
        self._compressRequest = compressRequest
        self._acceptCompressedResponse = acceptCompressedResponse

    def _request(self, methodName, args, keywords):
        """Call a method on the remote server."""
        request = {
            'version':  __version__,
            'action': 'call', 'methodName': methodName,
            'args': args, 'keywords':  keywords
        }
        request = dumps(request, -1 if self._binary else 0)
        if self._compressRequest and len(request) > 1000:
            request = zlib.compress(request, 1)
            compressed = True
        else:
            compressed = False

        response = self._transport.request(
            self._host, self._handler, request,
            verbose=self._verbose, binary=self._binary, compressed=compressed,
            acceptCompressedResponse=self._acceptCompressedResponse)

        return response

    def _requestValue(self, methodName, args, keywords):
        d = self._request(methodName, args, keywords)
        if 'value' in d:
            return d['value']
        if 'exception' in d:
            raise ResponseError(d['exception'])
        if 'requestError' in d:
            raise RequestError(d['requestError'])
        raise RequestError(
            'Response does not have a value, exception or requestError.')

    def __repr__(self):
        return f'<{self.__class__.__name__} for {self._host}{self._handler}>'

    __str__ = __repr__

    def __getattr__(self, name):
        """Magic method dispatcher.

        Note: to call a remote object with an non-standard name,
        use result getattr(server, "strange-python-name")(args)
        """
        return _Method(self._requestValue, name)


ServerProxy = Server  # be like xmlrpclib for those who might guess/expect it


class _Method:
    """Some magic to bind a Pickle-RPC method to an RPC server.

    Supports "nested" methods (e.g. examples.getStateName).
    """

    def __init__(self, send, name):
        self._send = send
        self._name = name

    def __getattr__(self, name):
        return _Method(self._send, f'{self._name}.{name}')

    def __call__(self, *args, **keywords):  # note that keywords are supported
        return self._send(self._name, args, keywords)


# pylint: disable=arguments-differ,invalid-name,unused-argument

class Transport(SafeUnpickler):
    """Handle an HTTP transaction to a Pickle-RPC server."""

    # client identifier (may be overridden)
    user_agent = f'PickleRPC/{__version__} (Webware for Python)'

    def request(self, host, handler, request_body,
                verbose=False, binary=False, compressed=False,
                acceptCompressedResponse=False):
        """Issue a Pickle-RPC request."""

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        self.send_user_agent(h)
        self.send_content(
            h, request_body, binary, compressed, acceptCompressedResponse)

        response = h.getresponse()
        h.headers, h.file = response.msg, response.fp

        if response.status != 200:
            raise ProtocolError(
                host + handler, response.status, response.reason, h.headers)

        self.verbose = verbose

        if h.headers['content-type'] not in (
                'text/x-python-pickled-dict',
                'application/x-python-binary-pickled-dict'):
            headers = h.headers.headers
            content = h.file.read()
            raise InvalidContentTypeError(headers, content)

        try:
            content_encoding = h.headers['content-encoding']
            if content_encoding and content_encoding == 'x-gzip':
                return self.parse_response_gzip(h.file)
            if content_encoding:
                raise ProtocolError(
                    host + handler, 500,
                    f'Unknown encoding type: {content_encoding}', h.headers)
            return self.parse_response(h.file)
        except KeyError:
            return self.parse_response(h.file)

    def make_connection(self, host, port=None):
        """Create an HTTP connection object from a host descriptor."""
        import http.client
        return http.client.HTTPConnection(host, port)

    def send_request(self, connection, handler, request_body):
        """Send request."""
        connection.putrequest('POST', handler)

    def send_host(self, connection, host):
        """Send host header."""
        connection.putheader('Host', host)

    def send_user_agent(self, connection):
        """Send user-agent header."""
        connection.putheader('User-Agent', self.user_agent)

    def send_content(self, connection, request_body,
                     binary=False, compressed=False,
                     acceptCompressedResponse=False):
        """Send content."""
        connection.putheader(
            'Content-Type',
            'application/x-python-binary-pickled-dict' if binary
            else 'text/x-python-pickled-dict')
        connection.putheader('Content-Length', str(len(request_body)))
        if compressed:
            connection.putheader('Content-Encoding', 'x-gzip')
        if zlib is not None and acceptCompressedResponse:
            connection.putheader('Accept-Encoding', 'gzip')
        connection.endheaders()
        if request_body:
            connection.send(request_body)

    def parse_response(self, f):
        """Read response from input file and parse it."""
        return self.load(f)

    def parse_response_gzip(self, f):
        """Read response from input file, decompress it, and parse it."""
        return self.loads(zlib.decompress(f.read()))


class SafeTransport(Transport):
    """Handle an HTTPS transaction to a Pickle-RPC server."""

    def make_connection(self, host, port=None, key_file=None, cert_file=None):
        """Create an HTTPS connection object from a host descriptor."""
        try:
            from http.client import HTTPSConnection
        except ImportError as e:
            raise NotImplementedError(
                "Your version of http.client doesn't support HTTPS") from e
        return HTTPSConnection(host, port, key_file, cert_file)
