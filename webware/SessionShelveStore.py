"""Session store using the shelve module."""

import os
import shelve
import threading

from MiscUtils import NoDefault

from SessionStore import maxPickleProtocol, SessionStore


class SessionShelveStore(SessionStore):
    """A session store implemented with a shelve object.

    To use this store, set SessionStore in Application.config to 'Shelve'.
    """

    _filename = 'Session.Store'

    # region Init

    def __init__(self, app, restoreFiles=None, filename=None):
        """Initialize the session shelf.

        If restoreFiles is true, existing shelve file(s) will be reused.
        """
        SessionStore.__init__(self, app)
        filename = os.path.join(app._sessionDir, filename or self._filename)
        if restoreFiles is None:
            restoreFiles = self._retain
        flag = 'c' if restoreFiles else 'n'
        self._store = shelve.open(
            filename, flag=flag, protocol=maxPickleProtocol)
        self._lock = threading.RLock()

    # endregion Init

    # region Access

    def __len__(self):
        """Return the number of sessions."""
        return len(self._store)

    def __getitem__(self, key):
        """Get a session item, reading it from the store."""
        # multiple simultaneous read accesses are safe
        return self._store[key]

    def __setitem__(self, key, value):
        """Set a session item, writing it to the store."""
        # concurrent write access is not supported
        dirty = value.isDirty()
        if self._alwaysSave or dirty:
            with self._lock:
                if dirty:
                    value.setDirty(False)
                try:
                    self._store[key] = value
                except Exception:
                    if dirty:
                        value.setDirty()
                    raise  # raise original exception

    def __delitem__(self, key):
        """Delete a session item from the store."""
        with self._lock:
            session = self[key]
            if not session.isExpired():
                session.expiring()
            del self._store[key]

    def __contains__(self, key):
        """Check whether the session store has a given key."""
        return key in self._store

    def __iter__(self):
        """Return an iterator over the stored session keys."""
        return iter(self._store)

    def keys(self):
        """Return a list with the keys of all the stored sessions."""
        return list(self._store.keys())

    def clear(self):
        """Clear the session store, removing all of its items."""
        self._store.clear()

    def setdefault(self, key, default=None):
        """Return value if key available, else default (also setting it)."""
        with self._lock:
            return self._store.setdefault(key, default)

    def pop(self, key, default=NoDefault):
        """Return value if key available, else default (also remove key)."""
        with self._lock:
            if default is NoDefault:
                return self._store.pop(key)
            return self._store.pop(key, default)

    # endregion Access

    # region Application support

    def storeSession(self, session):
        """Save potentially changed session in the store."""
        key = session.identifier()
        if key not in self or self[key] is not session:
            self[key] = session

    def storeAllSessions(self):
        """Permanently save all sessions in the store.

        Should be used (only) when the application server is shut down.
        """
        self._store.close()

    def cleanStaleSessions(self, task=None):
        """Clean stale sessions."""
        SessionStore.cleanStaleSessions(self, task)
        self.intervalSweep()

    def intervalSweep(self):
        """The session sweeper interval function."""
        self._store.sync()

    # endregion Application support
