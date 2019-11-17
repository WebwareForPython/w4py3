"""JSON-RPC servlet base class

Written by Jean-Francois Pieronne
"""

from json import dumps, loads
from io import StringIO
from traceback import print_exc

from HTTPContent import HTTPContent


class JSONRPCServlet(HTTPContent):
    """A superclass for Webware servlets using JSON-RPC techniques.

    JSONRPCServlet can be used to make coding JSON-RPC applications easier.

    Subclasses should override the method json_methods() which returns a list
    of method names. These method names refer to Webware Servlet methods that
    are able to be called by an JSON-RPC-enabled web page. This is very similar
    in functionality to Webware's actions.

    Some basic security measures against JavaScript hijacking are taken by
    default which can be deactivated if you're not dealing with sensitive data.
    You can further increase security by adding shared secret mechanisms.
    """

    # Class level variables that can be overridden by servlet instances:
    _debug = False  # set to True if you want to see debugging output
    # The following variables control security precautions concerning
    # a vulnerability known as "JavaScript hijacking".
    _allowGet = False  # set to True if you want to allow GET requests
    _allowEval = False  # set to True to allow direct evaluation of response

    def __init__(self):
        HTTPContent.__init__(self)

    def respondToGet(self, transaction):
        if self._allowGet:
            self.writeError("GET method not allowed")
        HTTPContent.respondToGet(self, transaction)

    def defaultAction(self):
        self.jsonCall()

    def actions(self):
        actions = HTTPContent.actions(self)
        actions.append('jsonCall')
        return actions

    @staticmethod
    def exposedMethods():
        """Return a list or a set of all exposed RPC methods."""
        return []

    def writeError(self, msg):
        self.write(dumps({'id': self._id, 'code': -1, 'error': msg}))

    def writeResult(self, data):
        data = dumps({'id': self._id, 'result': data})
        if not self._allowEval:
            data = ('throw new Error'
                    f'("Direct evaluation not allowed");\n/*{data}*/')
        self.write(data)

    def jsonCall(self):
        """Execute method with arguments on the server side.

        Returns JavaScript function to be executed by the client immediately.
        """
        self.response().setHeader('Content-Type', 'application/json')
        request = self.request()
        data = loads(request.rawInput().read())
        self._id, call, params = data['id'], data['method'], data['params']
        if call == 'system.listMethods':
            self.writeResult(self.exposedMethods())
        elif call in self.exposedMethods():
            try:
                method = getattr(self, call)
            except AttributeError:
                self.writeError(
                    f'{call}, although an approved method, was not found')
            else:
                try:
                    if self._debug:
                        self.log(f"json call {call}(call)")
                    if isinstance(params, list):
                        result = method(*params)
                    elif isinstance(params, dict):
                        result = method(**params)
                    else:
                        result = method()
                    self.writeResult(result)
                except Exception:
                    err = StringIO()
                    print_exc(file=err)
                    e = err.getvalue()
                    self.writeError(f'{call} was called,'
                                    f' but encountered an error: {e}')
                    err.close()
        else:
            self.writeError(f'{call} is not an approved method')
