"""Content producing HTTP servlet."""

from WebUtils.Funcs import urlDecode, urlEncode
from HTTPServlet import HTTPServlet
from Application import EndResponse


class HTTPContentError(Exception):
    """HTTP content error"""


class HTTPContent(HTTPServlet):
    """Content producing HTTP servlet.

    HTTPContent is a type of HTTPServlet that is more convenient for
    Servlets which represent content generated in response to
    GET and POST requests.  If you are generating HTML content, you
    you probably want your servlet to inherit from Page, which contains
    many HTML-related convenience methods.

    If you are generating non-HTML content, it is appropriate to inherit
    from this class directly.

    Subclasses typically override defaultAction().

    In `awake`, the page sets self attributes: `_transaction`, `_response`
    and `_request` which subclasses should use as appropriate.

    For the purposes of output, the `write` and `writeln`
    convenience methods are provided.

    If you plan to produce HTML content, you should start by looking
    at Page instead of this lower-level class.
    """

    # region Transactions

    def awake(self, transaction):
        """Let servlet awake.

        Makes instance variables from the transaction. This is where Page
        becomes unthreadsafe, as the page is tied to the transaction.
        This is also what allows us to implement functions like `write`,
        where you don't need to pass in the transaction or response.
        """
        HTTPServlet.awake(self, transaction)
        self._response = transaction.response()
        self._request = transaction.request()
        self._session = None  # don't create unless needed

    def respondToGet(self, transaction):
        """Respond to GET.

        Invoked in response to a GET request method. All methods
        are passed to `_respond`.
        """
        self._respond(transaction)

    def respondToPost(self, transaction):
        """Respond to POST.

        Invoked in response to a POST request method. All methods
        are passed to `_respond`.
        """
        self._respond(transaction)

    def _respond(self, transaction):
        """Respond to action.

        Handles actions if an ``_action_`` or ``_action_name`` field is
        defined, otherwise invokes `writeHTML`. This implementation makes
        sure that exactly one action per request is handled. ``_action_``
        takes precedence over ``_action_name``; and if there are multiple
        ``action_name`` fields, the precedence is given by the order of
        the names in the actions() method. If no action field matches,
        the default action is run. The value of the ``_action_`` field
        is transformed to a method name using the methodNameForAction(),
        whereas ``name`` in ``_action_name`` is left unchanged.

        Invoked by both `respondToGet` and `respondToPost`.
        """
        req = transaction.request()
        prefix = self._actionPrefix
        if prefix:
            # First check whether there is an _action_ field:
            if req.hasField(prefix):
                action = self.methodNameForAction(req.field(prefix))
                if action in self.actions():
                    self.handleAction(action)
                    return
            # Next, check whether there is an _action_name field:
            for action in self.actions():
                name = prefix + action
                if req.hasField(name) or (
                        req.hasField(name + '.x')
                        and req.hasField(name + '.y')):
                    self.handleAction(action)
                    return
            # If no action was found, run the default:
        self.defaultAction()

    def defaultAction(self):
        """Default action.

        The core method that gets called as a result of requests.
        Subclasses should override this.
        """
        # base method does nothing

    def sleep(self, transaction):
        """Let servlet sleep again.

        We unset some variables. Very boring.
        """
        self._session = None
        self._request = None
        self._response = None
        self._transaction = None
        HTTPServlet.sleep(self, transaction)

    # endregion Transactions

    # region Access

    def application(self):
        """The `Application` instance we're using."""
        return self._transaction.application()

    def transaction(self):
        """The `Transaction` we're currently handling."""
        return self._transaction

    def request(self):
        """The request (`HTTPRequest`) we're handling."""
        return self._request

    def response(self):
        """The response (`HTTPResponse`) we're handling."""
        return self._response

    def session(self):
        """The session object.

        This provides a state for the current user
        (associated with a browser instance, really).
        If no session exists, then a session will be created.
        """
        if not self._session:
            self._session = self._transaction.session()
        return self._session

    # endregion Access

    # region Writing

    def write(self, *args):
        """Write to output.

        Writes the arguments, which are turned to strings (with `str`)
        and concatenated before being written to the response.
        Unicode strings must be encoded before they can be written.
        """
        for arg in args:
            self._response.write(arg)

    def writeln(self, *args):
        """Write to output with newline.

        Writes the arguments (like `write`), adding a newline after.
        Unicode strings must be encoded before they can be written.
        """
        for arg in args:
            self._response.write(arg)
        self._response.write('\n')

    def outputEncoding(self):
        """Get the default output encoding of the application."""
        return self.application().outputEncoding()

    # endregion Writing

    # region Threading

    def canBeThreaded(self):
        """Declares whether servlet can be threaded.

        Returns False because of the instance variables we set up in `awake`.
        """
        return False

    # endregion Threading

    # region Actions

    _actionPrefix = '_action_'

    def handleAction(self, action):
        """Handle action.

        Invoked by `_respond` when a legitimate action has
        been found in a form. Invokes `preAction`, the actual
        action method and `postAction`.

        Subclasses rarely override this method.
        """
        self.preAction(action)
        getattr(self, action)()
        self.postAction(action)

    def actions(self):
        """The allowed actions.

        Returns a list or a set of method names that are allowable
        actions from HTML forms. The default implementation returns [].
        See `_respond` for more about actions.
        """
        return []

    def preAction(self, actionName):
        """Things to do before action.

        Invoked by self prior to invoking a action method.
        The `actionName` is passed to this method,
        although it seems a generally bad idea to rely on this.
        However, it's still provided just in case you need that hook.

        By default this does nothing.
        """
        # base method does nothing

    def postAction(self, actionName):
        """Things to do after action.

        Invoked by self after invoking a action method.
        Subclasses may override to customize and may or may not
        invoke super as they see fit.
        The `actionName` is passed to this method,
        although it seems a generally bad idea to rely on this.
        However, it's still provided just in case you need that hook.

        By default this does nothing.
        """
        # base method does nothing

    def methodNameForAction(self, name):
        """Return method name for an action name.

        Invoked by _respond() to determine the method name for a given action
        name which has been derived as the value of an ``_action_`` field.
        Since this is usually the label of an HTML submit button in a form,
        it is often needed to transform it in order to get a valid method name
        (for instance, blanks could be replaced by underscores and the like).
        This default implementation of the name transformation is the identity,
        it simply returns the name. Subclasses should override this method
        when action names don't match their method names; they could "mangle"
        the action names or look the method names up in a dictionary.
        """
        return name

    @staticmethod
    def urlEncode(s):
        """Quotes special characters using the % substitutions.

        This method does the same as the `urllib.quote_plus()` function.
        """
        return urlEncode(s)

    @staticmethod
    def urlDecode(s):
        """Turn special % characters into actual characters.

        This method does the same as the `urllib.unquote_plus()` function.
        """
        return urlDecode(s)

    def forward(self, url):
        """Forward request.

        Forwards this request to another servlet.
        See `Application.forward` for details.
        The main difference is that here you don't have
        to pass in the transaction as the first argument.
        """
        self.application().forward(self.transaction(), url)

    def includeURL(self, url):
        """Include output from other servlet.

        Includes the response of another servlet
        in the current servlet's response.
        See `Application.includeURL` for details.
        The main difference is that here you don't have
        to pass in the transaction as the first argument.
        """
        self.application().includeURL(self.transaction(), url)

    def callMethodOfServlet(self, url, method, *args, **kwargs):
        """Call a method of another servlet.

        See `Application.callMethodOfServlet` for details.
        The main difference is that here you don't have
        to pass in the transaction as the first argument.
        """
        return self.application().callMethodOfServlet(
            self.transaction(), url, method, *args, **kwargs)

    @staticmethod
    def endResponse():
        """End response.

        When this method is called during `awake` or `respond`,
        servlet processing will end immediately,
        and the accumulated response will be sent.

        Note that `sleep` will still be called, providing a
        chance to clean up or free any resources.
        """
        raise EndResponse

    def sendRedirectAndEnd(self, url, status=None):
        """Send redirect and end.

        Sends a redirect back to the client and ends the response.
        This is a very popular pattern.
        """
        self.response().sendRedirect(url, status)
        self.endResponse()

    def sendRedirectPermanentAndEnd(self, url):
        """Send permanent redirect and end."""
        self.response().sendRedirectPermanent(url)
        self.endResponse()

    def sendRedirectSeeOtherAndEnd(self, url):
        """Send redirect to a URL to be retrieved with GET and end.

        This is the proper method for the Post/Redirect/Get pattern.
        """
        self.response().sendRedirectSeeOther(url)
        self.endResponse()

    def sendRedirectTemporaryAndEnd(self, url):
        """Send temporary redirect and end."""
        self.response().sendRedirectTemporary(url)
        self.endResponse()

    # endregion Actions

    # region Utility

    def sessionEncode(self, url=None):
        """Utility function to access `Session.sessionEncode`.

        Takes a url and adds the session ID as a parameter.
        This is for cases where you don't know if the client
        will accepts cookies.
        """
        if url is None:
            url = self.request().uri()
        return self.session().sessionEncode(url)

    # endregion Utility

    # region Exception Reports

    def writeExceptionReport(self, handler):
        """Write extra information to the exception report.

        The `handler` argument is the exception handler, and information
        is written there (using `writeTitle`, `write`, and `writeln`).
        This information is added to the exception report.

        See `ExceptionHandler` for more information.
        """
        handler.writeln('''
<p>Servlets can provide debugging information here by overriding
<code>writeExceptionReport()</code>.</p><p>For example:</p>
<pre>
exceptionReportAttrs = ['foo', 'bar', 'baz']
def writeExceptionReport(self, handler):
    handler.writeTitle(self.__class__.__name__)
    handler.writeAttrs(self, self.exceptionReportAttrs)
    handler.write('any string')
</pre>
<p>See ExceptionHandler.py for more information.</p>
''')

    # endregion Exception Reports
