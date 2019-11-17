"""Implementation of client sessions."""

import re
from time import time, localtime
from urllib import parse

from MiscUtils import NoDefault
from MiscUtils.Funcs import uniqueId


class SessionError(Exception):
    """Client session error"""


class Session:
    """Implementation of client sessions.

    All methods that deal with time stamps, such as creationTime(),
    treat time as the number of seconds since January 1, 1970.

    Session identifiers are stored in cookies. Therefore, clients
    must have cookies enabled.

    Note that the session id should be a string that is valid
    as part of a filename. This is currently true, and should
    be maintained if the session id generation technique is
    modified. Session ids can be used in filenames.
    """

    # region Init

    def __init__(self, trans, identifier=None):
        self._lastAccessTime = self._creationTime = time()
        self._isExpired = self._dirty = False
        self._numTrans = 0
        self._values = {}
        app = trans.application()
        self._timeout = app.sessionTimeout(trans)
        self._prefix = app.sessionPrefix(trans)
        self._sessionName = app.sessionName(trans)

        if identifier:
            if re.search(r'[^\w\.\-]', identifier) is not None:
                raise SessionError("Illegal characters in session identifier")
            if len(identifier) > 80:
                raise SessionError("Session identifier too long")
            self._identifier = identifier
        else:
            attempts = 0
            while attempts < 10000:
                self._identifier = self._prefix + (
                    '{:02d}{:02d}{:02d}{:02d}{:02d}{:02d}').format(
                        *localtime()[:6]) + '-' + uniqueId(self)
                if not app.hasSession(self._identifier):
                    break
                attempts += 1
            else:
                raise SessionError(
                    "Can't create valid session id"
                    f" after {attempts} attempts.")

        if app.setting('Debug')['Sessions']:
            print('>> [session] Created session, timeout =', self._timeout,
                  'id =', self._identifier, 'self =', self)

    # endregion Init

    # region Access

    def creationTime(self):
        """Return the time when this session was created."""
        return self._creationTime

    def lastAccessTime(self):
        """Get last access time.

        Returns the last time the user accessed the session through
        interaction. This attribute is updated in awake(), which is
        invoked at the beginning of a transaction.
        """
        return self._lastAccessTime

    def identifier(self):
        """Return a string that uniquely identifies the session.

        This method will create the identifier if needed.
        """
        return self._identifier

    def isDirty(self):
        """Check whether the session is dirty (has unsaved changes)."""
        return self._dirty

    def setDirty(self, dirty=True):
        """Set the dirty status of the session."""
        self._dirty = dirty

    def isExpired(self):
        """Check whether the session has been previously expired.

        See also: expiring()
        """
        return getattr(self, '_isExpired', False) or self._timeout == 0

    def isNew(self):
        """Check whether the session is new."""
        return self._numTrans < 2

    def timeout(self):
        """Return the timeout for this session in seconds."""
        return self._timeout

    def setTimeout(self, timeout):
        """Set the timeout on this session in seconds."""
        self._timeout = timeout

    # endregion Access

    # region Invalidate

    def invalidate(self):
        """Invalidate the session.

        It will be discarded the next time it is accessed.
        """
        self._lastAccessTime = 0
        self._values = {}
        self._dirty = False
        self._timeout = 0

    # endregion Invalidate

    # region Values

    def value(self, name, default=NoDefault):
        if default is NoDefault:
            return self._values[name]
        return self._values.get(name, default)

    def hasValue(self, name):
        return name in self._values

    def setValue(self, name, value):
        self._values[name] = value
        self._dirty = True

    def delValue(self, name):
        del self._values[name]
        self._dirty = True

    def values(self):
        return self._values

    def __getitem__(self, name):
        return self.value(name)

    def __setitem__(self, name, value):
        self.setValue(name, value)

    def __delitem__(self, name):
        self.delValue(name)

    def __contains__(self, name):
        return self.hasValue(name)

    # endregion Values

    # region Transactions

    def awake(self, _trans):
        """Let the session awake.

        Invoked during the beginning of a transaction, giving a Session an
        opportunity to perform any required setup. The default implementation
        updates the 'lastAccessTime'.
        """
        self._lastAccessTime = time()
        self._numTrans += 1

    def respond(self, trans):
        """Let the session respond to a request.

        The default implementation does nothing, but could do something
        in the future. Subclasses should invoke super.
        """
        # base method does nothing

    def sleep(self, trans):
        """Let the session sleep again.

        Invoked during the ending of a transaction, giving a Session an
        opportunity to perform any required shutdown. The default
        implementation does nothing, but could do something in the future.
        Subclasses should invoke super.
        """
        # base method does nothing

    def expiring(self):
        """Let the session expire.

        Called when session is expired by the application.
        Subclasses should invoke super.
        Session store __delitem__()s should invoke if not isExpired().
        """
        self._isExpired = True

    def numTransactions(self):
        """Get number of transactions.

        Returns the number of transactions in which the session has been used.
        """
        return self._numTrans

    # endregion Transactions

    # region Utility

    def sessionEncode(self, url):
        """Encode the session ID as a parameter to a url."""
        url = list(parse.urlparse(url))  # make a list
        if url[4]:
            url[4] += '&'
        url[4] += f'{self._sessionName}={self.identifier()}'
        url = parse.urlunparse(url)
        return url

    # endregion Utility

    # region Exception reports

    _exceptionReportAttrNames = [
        'isDirty', 'isExpired', 'lastAccessTime',
        'numTransactions', 'timeout', 'values']

    def writeExceptionReport(self, handler):
        handler.writeTitle(self.__class__.__name__)
        handler.writeAttrs(self, self._exceptionReportAttrNames)

    # endregion Exception reports
