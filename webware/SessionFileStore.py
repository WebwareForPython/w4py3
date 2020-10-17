"""Session store using files."""

import os
import threading

from MiscUtils import NoDefault

from SessionStore import SessionStore


class SessionFileStore(SessionStore):
    """A session file store.

    Stores the sessions on disk in the Sessions/ directory,
    one file per session.
    """

    _extension = '.ses'

    # region Init

    def __init__(self, app, restoreFiles=None):
        """Initialize the session file store.

        If restoreFiles is true, and sessions have been saved to file,
        the store will be initialized from these files.
        """
        SessionStore.__init__(self, app)
        if restoreFiles is None:
            restoreFiles = self._retain
        self._sessionDir = app._sessionDir
        self._lock = threading.RLock()
        if not restoreFiles:
            self.clear()

    # endregion Init

    # region Access

    def __len__(self):
        """Return the number of sessions in the store."""
        return len(self.keys())

    def __getitem__(self, key):
        """Get a session item, loading it from the session file."""
        filename = self.filenameForKey(key)
        with self._lock:
            try:
                sessionFile = open(filename, 'rb')
            except IOError as e:
                raise KeyError(key) from e  # session file not found
            try:
                try:
                    value = self.decoder()(sessionFile)
                finally:
                    sessionFile.close()
            except Exception as e:
                print("Error loading session from disk:", key)
                self.application().handleException()
                try:  # remove the session file because it is corrupt
                    os.remove(filename)
                except Exception:
                    pass
                raise KeyError(key) from e
        return value

    def __setitem__(self, key, value):
        """Set a session item, saving it to a session file."""
        dirty = value.isDirty()
        if self._alwaysSave or dirty:
            filename = self.filenameForKey(key)
            with self._lock:
                if dirty:
                    value.setDirty(False)
                try:
                    sessionFile = open(filename, 'wb')
                    try:
                        try:
                            self.encoder()(value, sessionFile)
                        finally:
                            sessionFile.close()
                    except Exception:
                        # remove the session file because it is corrupt
                        os.remove(filename)
                        raise  # raise original exception
                except Exception:  # error pickling the session
                    if dirty:
                        value.setDirty()
                    print("Error saving session to disk:", key)
                    self.application().handleException()

    def __delitem__(self, key):
        """Delete a session item, removing its session file."""
        filename = self.filenameForKey(key)
        if not os.path.exists(filename):
            raise KeyError(key)
        session = self[key]
        if not session.isExpired():
            session.expiring()
        try:
            os.remove(filename)
        except Exception:
            pass

    def __contains__(self, key):
        """Check whether the session store has a file for the given key."""
        return os.path.exists(self.filenameForKey(key))

    def __iter__(self):
        """Return an iterator over the stored session keys."""
        ext = self._extension
        pos = -len(ext)
        # note that iglob is slower here, since it's based on listdir
        for filename in os.listdir(self._sessionDir):
            if filename.endswith(ext):
                yield filename[:pos]

    def removeKey(self, key):
        """Remove the session file for the given key."""
        filename = self.filenameForKey(key)
        try:
            os.remove(filename)
        except Exception:
            pass

    def keys(self):
        """Return a list with the keys of all the stored sessions."""
        return list(iter(self))

    def clear(self):
        """Clear the session file store, removing all of the session files."""
        for key in self:
            self.removeKey(key)

    def setdefault(self, key, default=None):
        """Return value if key available, else default (also setting it)."""
        with self._lock:
            try:
                return self[key]
            except KeyError:
                self[key] = default
                return default

    def pop(self, key, default=NoDefault):
        """Return value if key available, else default (also remove key)."""
        with self._lock:
            if default is NoDefault:
                value = self[key]
                self.removeKey(key)
                return value
            if key in self:
                return self[key]
            return default

    # endregion Access

    # region Application support

    def storeSession(self, session):
        """Save session, writing it to the session file now."""
        if self._alwaysSave or session.isDirty():
            self[session.identifier()] = session

    def storeAllSessions(self):
        """Permanently save all sessions in the store."""
        # sessions have all been saved to files already

    # endregion Application support

    # region Self utility

    def filenameForKey(self, key):
        """Return the name of the session file for the given key."""
        return os.path.join(self._sessionDir, key + self._extension)

    # endregion Self utility
