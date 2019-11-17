"""RPC servlets."""

import traceback
import sys

from HTTPServlet import HTTPServlet


class RPCServlet(HTTPServlet):
    """RPCServlet is a base class for RPC servlets."""

    def call(self, methodName, *args, **keywords):
        """Call custom method.

        Subclasses may override this class for custom handling of methods.
        """
        if methodName not in self.exposedMethods():
            raise NotImplementedError(methodName)
        return getattr(self, methodName)(*args, **keywords)

    @staticmethod
    def exposedMethods():
        """Get exposed methods.

        Subclasses should return a list of methods that will be exposed
        through XML-RPC.
        """
        return ['exposedMethods']

    def resultForException(self, e, trans):
        """Get text for exception.

        Given an unhandled exception, returns the string that should be
        sent back in the RPC response as controlled by the
        RPCExceptionReturn setting.
        """
        # report exception back to server
        setting = trans.application().setting('RPCExceptionReturn')
        if setting == 'occurred':
            result = 'unhandled exception'
        elif setting == 'exception':
            result = str(e)
        elif setting == 'traceback':
            result = ''.join(traceback.format_exception(*sys.exc_info()))
        else:
            raise ValueError(f'Invalid setting: {setting!r}')
        return result

    @staticmethod
    def sendOK(contentType, contents, trans, contentEncoding=None):
        """Send a 200 OK response with the given contents."""
        response = trans.response()
        response.setStatus(200, 'OK')
        response.setHeader('Content-Type', contentType)
        response.setHeader('Content-Length', str(len(contents)))
        if contentEncoding:
            response.setHeader('Content-Encoding', contentEncoding)
        response.write(contents)

    @staticmethod
    def handleException(transaction):
        """Handle exception.

        If ReportRPCExceptionsInWebware is set to True, then flush the response
        (because we don't want the standard HTML traceback to be appended to
        the response) and then handle the exception in the standard Webware
        way. This means logging it to the console, storing it in the error log,
        sending error email, etc. depending on the settings.
        """
        setting = transaction.application().setting(
            'ReportRPCExceptionsInWebware')
        if setting:
            transaction.response().flush()
            transaction.application().handleExceptionInTransaction(
                sys.exc_info(), transaction)

    def transaction(self):
        """Get the corresponding transaction.

        Most uses of RPC will not need this.
        """
        return self._transaction

    def awake(self, transaction):
        """Begin transaction."""
        HTTPServlet.awake(self, transaction)
        self._transaction = transaction

    def sleep(self, transaction):
        """End transaction."""
        self._transaction = None
        HTTPServlet.sleep(self, transaction)
