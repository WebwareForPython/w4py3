"""Session store in memory."""

from MiscUtils import NoDefault

from SessionStore import SessionStore
from SessionFileStore import SessionFileStore


class SessionMemoryStore(SessionStore):
    """Stores the session in memory as a dictionary.

    This is fast and secure when you have one, persistent application instance.
    """

    # region Init

    def __init__(self, app, restoreFiles=None):
        """Initialize the session memory store.

        If restoreFiles is true, and sessions have been saved to file,
        the store will be initialized from these files.
        """
        SessionStore.__init__(self, app)
        self._store = {}
        if restoreFiles is None:
            restoreFiles = self._retain
        if restoreFiles:
            fileStore = SessionFileStore(app)
            for key in fileStore:
                try:
                    self[key] = fileStore[key]
                except Exception:
                    app.handleException()
            fileStore.clear()
        self._restoreFiles = restoreFiles

    # endregion Init

    # region Access

    def __len__(self):
        """Return the number of sessions in the store."""
        return len(self._store)

    def __getitem__(self, key):
        """Get a session item from the store."""
        return self._store[key]

    def __setitem__(self, key, value):
        """Set a session item, saving it to the store."""
        value.setDirty(False)
        self._store[key] = value

    def __delitem__(self, key):
        """Delete a session item from the store."""
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
        return list(self._store)

    def clear(self):
        """Clear the session store, removing all of its items."""
        self._store.clear()

    def setdefault(self, key, default=None):
        """Return value if key available, else default (also setting it)."""
        # note that setdefault() is atomic, so no locking is needed
        return self._store.setdefault(key, default)

    def pop(self, key, default=NoDefault):
        """Return value if key available, else default (also remove key)."""
        # note that pop() is atomic, so no locking is needed
        if default is NoDefault:
            return self._store.pop(key)
        return self._store.pop(key, default)

    # endregion Access

    # region Application support

    def storeSession(self, session):
        """Save already potentially changed session in the store."""
        if self._alwaysSave or session.isDirty():
            key = session.identifier()
            if key not in self or self[key] is not session:
                self[key] = session

    def storeAllSessions(self):
        """Permanently save all sessions in the store."""
        if self._restoreFiles:
            fileStore = SessionFileStore(self._app)
            for key, session in list(self.items()):
                fileStore[key] = session

    # endregion Application support
