"""The Transaction container."""

import sys
import traceback


class Transaction:
    """The Transaction container.

    A transaction serves as:

      * A container for all objects involved in the transaction.
        The objects include application, request, response, session
        and servlet.

      * A message dissemination point. The messages include awake(),
        respond() and sleep().

    When first created, a transaction has no session. However, it will
    create or retrieve one upon being asked for session().

    The life cycle of a transaction begins and ends with Application's
    dispatchRequest().
    """

    # region Init

    def __init__(self, application, request=None):
        self._application = application
        self._request = request
        self._response = None
        self._session = None
        self._servlet = None
        self._error = None
        self._nested = 0

    def __repr__(self):
        s = []
        for name in sorted(self.__dict__):
            attr = getattr(self, name)
            if isinstance(attr, type):
                s.append(f'{name}={attr!r}')
        s = ' '.join(s)
        return f'<{self.__class__.__name__} {s}>'

    # endregion Init

    # region Access

    def application(self):
        """Get the corresponding application."""
        return self._application

    def request(self):
        """Get the corresponding request."""
        return self._request

    def response(self):
        """Get the corresponding response."""
        return self._response

    def setResponse(self, response):
        """Set the corresponding response."""
        self._response = response

    def hasSession(self):
        """Return true if the transaction has a session."""
        sid = self._request.sessionId()
        return sid and self._application.hasSession(sid)

    def session(self):
        """Return the session for the transaction.

        A new transaction is created if necessary. Therefore, this method
        never returns None. Use hasSession() if you want to find out if
        a session already exists.
        """
        if not self._session:
            self._session = self._application.createSessionForTransaction(self)
            self._session.awake(self)  # give new servlet a chance to set up
        return self._session

    def setSession(self, session):
        """Set the session for the transaction."""
        self._session = session

    def servlet(self):
        """Return the current servlet that is processing.

        Remember that servlets can be nested.
        """
        return self._servlet

    def setServlet(self, servlet):
        """Set the servlet for processing the transaction."""
        self._servlet = servlet
        if servlet and self._request:
            servlet._serverSidePath = self._request.serverSidePath()

    def duration(self):
        """Return the duration, in seconds, of the transaction.

        This is basically the response end time minus the request start time.
        """
        return self._response.endTime() - self._request.time()

    def errorOccurred(self):
        """Check whether a server error occurred."""
        return isinstance(self._error, Exception)

    def error(self):
        """Return Exception instance if there was any."""
        return self._error

    def setError(self, err):
        """Set Exception instance.

        Invoked by the application if an Exception is raised to the
        application level.
        """
        self._error = err

    # endregion Access

    # region Transaction stages

    def awake(self):
        """Send awake() to the session (if there is one) and the servlet.

        Currently, the request and response do not partake in the
        awake()-respond()-sleep() cycle. This could definitely be added
        in the future if any use was demonstrated for it.
        """
        if not self._nested and self._session:
            self._session.awake(self)
        self._servlet.awake(self)
        self._nested += 1

    def respond(self):
        """Respond to the request."""
        if self._session:
            self._session.respond(self)
        self._servlet.respond(self)

    def sleep(self):
        """Send sleep() to the session and the servlet.

        Note that sleep() is sent in reverse order as awake()
        (which is typical for shutdown/cleanup methods).
        """
        self._nested -= 1
        self._servlet.sleep(self)
        if not self._nested and self._session:
            self._session.sleep(self)
            self._application.sessions().storeSession(self._session)

    # endregion Transaction stages

    # region Debugging

    def dump(self, file=None):
        """Dump debugging info to stdout."""
        if file is None:
            file = sys.stdout
        wr = file.write
        wr(f'>> Transaction: {self}\n')
        for attr in dir(self):
            wr(f'{attr}: {getattr(self, attr)}\n')
        wr('\n')

    # endregion Debugging

    # region Die

    def die(self):
        """End transaction.

        This method should be invoked when the entire transaction is finished
        with. Currently, this is invoked by the Application. This method
        removes references to the different objects in the transaction,
        breaking cyclic reference chains and speeding up garbage collection.
        """
        keys = list(self.__dict__)
        for name in keys:
            delattr(self, name)

    # endregion Die

    # region Exception handling

    _exceptionReportAttrNames = (
        'application request response session servlet').split()

    def writeExceptionReport(self, handler):
        """Write extra information to the exception report."""
        handler.writeTitle(self.__class__.__name__)
        handler.writeAttrs(self, self._exceptionReportAttrNames)

        for name in self._exceptionReportAttrNames:
            obj = getattr(self, '_' + name, None)
            if obj:
                try:
                    obj.writeExceptionReport(handler)
                except Exception:
                    handler.writeln(
                        '<p>Uncaught exception while asking'
                        f' <strong>{name}</strong> to write report:</p>')
                    handler.writeln('<pre>')
                    traceback.print_exc(file=handler)
                    handler.writeln('</pre>')

    # endregion Exception handling
