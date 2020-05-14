"""AJAX page template class

Written by John Dickinson based on ideas from
Apple Developer Connection and DivMod Nevow.
Some changes by Robert Forkel and Christoph Zwerschke.
"""

from time import time
from traceback import print_exc
from random import randrange

from io import StringIO

from .ExamplePage import ExamplePage as BaseClass


def quoteJs(what):
    """Return quoted JavaScript string corresponding to the Python object."""
    if isinstance(what, bool):
        ret = str(what).lower()
    elif isinstance(what, (int, float, PyJs)):
        ret = str(what)
    else:
        ret = "'{}'".format(str(what).replace('\\', '\\\\').replace(
            '\'', '\\\'').replace('\n', '\\n'))
    return ret


class PyJs:
    """Translate Python expressions to JavaScript strings."""

    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr):
        return self.__class__(f'{self}.{attr}')

    def __str__(self):
        return self._name

    def __call__(self, *args, **kw):
        args = ','.join(map(quoteJs, args))
        kwArgs = ','.join(f'{k}={quoteJs(v)}' for k, v in kw.items())
        if args and kwArgs:
            allArgs = f'{args},{kwArgs}'
        elif not kwArgs:
            allArgs = args
        elif not args:
            allArgs = kwArgs
        return self.__class__(f'{self}({allArgs}')

    def __getitem__(self, index):
        return self.__class__(f'{self}[{quoteJs(index)}]')

    def __repr__(self):
        return self.__str__()


class AjaxPage(BaseClass):
    """A superclass for Webware servlets using Ajax techniques.

    AjaxPage can be used to make coding XMLHttpRequest() applications easier.

    Subclasses should override the method exposedMethods() which returns a list
    of method names. These method names refer to Webware Servlet methods that
    are able to be called by an Ajax-enabled web page. This is very similar
    in functionality to Webware's actions.

    A polling mechanism can be used for long running requests (e.g. generating
    reports) or if you want to send commands to the client without the client
    first triggering an event (e.g. for a chat application). In the first case,
    you should also specify a timeout after which polling shall be used.
    """

    # Class level variables that can be overridden by servlet instances:
    _debug = False  # set to True if you want to see debugging output
    _clientPolling = True  # set to True if you want to use polling
    _responseTimeout = 90  # timeout of client waiting for response in seconds

    # Class level variables to help make client code simpler:
    window, document, alert, this = map(
        PyJs, 'window document alert this'.split())
    setTag, setClass, setID, setValue, setReadonly = map(
        PyJs, 'setTag setClass setID setValue setReadonly'.split())
    call, callForm = map(PyJs, ('ajax_call', 'ajax_call_form'))

    # Response Queue for timed out queries:
    _responseQueue = {}

    def writeJavaScript(self):
        BaseClass.writeJavaScript(self)
        s = '<script src="ajax{}.js"></script>'
        self.writeln(s.format('call'))
        if self._clientPolling:
            self.writeln(s.format('poll'))

    def actions(self):
        actions = BaseClass.actions(self)
        actions.append('ajaxCall')
        if self._clientPolling:
            actions.append('ajaxPoll')
        return actions

    def exposedMethods(self):
        return []

    @staticmethod
    def clientPollingInterval():
        """Set the interval for the client polling.

        You should always make it a little random to avoid synchronization.
        """
        return randrange(3, 8)

    def ajaxCall(self):
        """Execute method with arguments on the server side.

        The method name is passed in the field _call_,
        the unique request number in the field _req_
        and the arguments in the field _ (single underscore).

        Returns JavaScript function to be executed by the client immediately.
        """
        req = self.request()
        startTime = None
        if req.hasField('_call_'):
            call = req.field('_call_')
            args = req.field('_', [])
            if not isinstance(args, list):
                args = [args]
            if self._clientPolling and self._responseTimeout:
                startTime = time()
            if call in self.exposedMethods():
                try:
                    method = getattr(self, call)
                except AttributeError:
                    cmd = self.alert(
                        f'{call}, although an approved method, was not found')
                else:
                    try:
                        if self._debug:
                            self.log(f"Ajax call {call}({args})")
                        cmd = str(method(*args))
                    except Exception:
                        err = StringIO()
                        print_exc(file=err)
                        e = err.getvalue()
                        cmd = self.alert(
                            f'{call} was called,'
                            f' but encountered an error: {e}')
                        err.close()
            else:
                cmd = self.alert(f'{call} is not an approved method')
        else:
            cmd = self.alert('Ajax call missing call parameter.')
        inTime = startTime is None or (
            time() - startTime < self._responseTimeout)
        if inTime:
            # If the computation of the method did not last very long,
            # deliver it immediately back to the client with this response:
            if self._debug:
                self.log(f"Ajax returns immediately: {cmd}")
            self.response().setHeader('Content-Type', 'application/json')
            self.write(cmd)
        else:
            # If the client request might have already timed out,
            # put the result in the queue and let client poll it:
            if self._debug:
                self.log(f"Ajax puts in queue: {cmd}")
            sid = self.session().identifier()
            self._responseQueue.setdefault(sid, []).append(cmd)

    def ajaxPoll(self):
        """Return queued JavaScript functions to be executed on the client.

        This is polled by the client in random intervals in order to get
        results from long-running queries or push content to the client.
        """
        if self._clientPolling:
            sid = self.session().identifier()
            # Set the timeout until the next time this method is called
            # by the client, using the Javascript wait variable:
            cmd = [f'wait={self.clientPollingInterval()}']
            if sid in self._responseQueue:  # add in other commands
                cmd.extend(map(str, self._responseQueue[sid]))
                self._responseQueue[sid] = []
            cmd = ';'.join(cmd) + ';'
            if self._debug:
                self.log(f"Ajax returns from queue: {cmd}")
        else:
            if self._debug:
                self.log("Ajax tells the client to stop polling.")
            cmd = 'dying=true;'
        self.response().setHeader('Content-Type', 'application/json')
        self.write(cmd)  # write out at least the wait variable

    def ajaxPush(self, cmd):
        """Push JavaScript commands to be executed on the client.

        Client polling must be activated if you want to use this.
        """
        if self._clientPolling:
            if self._debug:
                self.log(f"Ajax pushes in queue: {cmd}")
            sid = self.session().identifier()
            self._responseQueue.setdefault(sid, []).append(cmd)

    def preAction(self, actionName):
        if actionName not in ('ajaxCall', 'ajaxPoll'):
            BaseClass.preAction(self, actionName)

    def postAction(self, actionName):
        if actionName not in ('ajaxCall', 'ajaxPoll'):
            BaseClass.postAction(self, actionName)
