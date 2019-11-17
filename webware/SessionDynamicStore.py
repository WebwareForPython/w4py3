"""Session store using memory and files."""

import time
import threading

from MiscUtils import NoDefault

import SessionMemoryStore
import SessionFileStore

from SessionStore import SessionStore

debug = False


class SessionDynamicStore(SessionStore):
    """Stores the session in memory and in files.

    To use this Session Store, set SessionStore in Application.config
    to 'Dynamic'. Other variables which can be set in Application.config are:

    'MaxDynamicMemorySessions', which sets the maximum number of sessions
    that can be in memory at one time. Default is 10,000.

    'DynamicSessionTimeout', which sets the default time for a session to stay
    in memory with no activity. Default is 15 minutes. When specifying this in
    Application.config, use minutes.

    One-shot sessions (usually created by crawler bots) aren't moved to
    FileStore on periodical clean-up. They are still saved on SessionStore
    shutdown. This reduces the number of files in the Sessions directory.
    """

    # region Init

    def __init__(self, app):
        """Create both a file and a memory store."""
        SessionStore.__init__(self, app)
        self._fileStore = SessionFileStore.SessionFileStore(app)
        self._memoryStore = SessionMemoryStore.SessionMemoryStore(
            app, restoreFiles=False)  # session files are read on demand

        # moveToFileInterval specifies after what period of time
        # in seconds a session is automatically moved to a file
        self._moveToFileInterval = app.setting(
            'DynamicSessionTimeout', 15) * 60

        # maxDynamicMemorySessions is what the user actually sets
        # in Application.config, the maximum number of in memory sessions
        self._maxDynamicMemorySessions = app.setting(
            'MaxDynamicMemorySessions', 10000)

        # Used to keep track of sweeping the file store
        self._fileSweepCount = 0

        # Create a re-entrant lock for thread synchronization. The lock is used
        # to protect all code that modifies the contents of the file store and
        # all code that moves sessions between the file and memory stores, and
        # is also used to protect code that searches in the file store for a
        # session. Using the lock in this way avoids a bug that used to be in
        # this code, where a session was temporarily neither in the file store
        # nor in the memory store while it was being moved from file to memory.
        self._lock = threading.RLock()

        if debug:
            print("SessionDynamicStore Initialized")

    # endregion Init

    # region Access

    def __len__(self):
        """Return the number of sessions in the store."""
        with self._lock:
            return len(self._memoryStore) + len(self._fileStore)

    def __getitem__(self, key):
        """Get a session item from the store."""
        # First try to grab the session from the memory store without locking,
        # for efficiency. Only if that fails do we acquire the lock and look
        # in the file store.
        try:
            return self._memoryStore[key]
        except KeyError:
            with self._lock:
                if key in self._fileStore:
                    self.moveToMemory(key)
                # let it raise a KeyError otherwise
                return self._memoryStore[key]

    def __setitem__(self, key, value):
        """Set a sessing item, saving it to the memory store for now."""
        value.setDirty(False)
        self._memoryStore[key] = value

    def __delitem__(self, key):
        """Delete a session item from the memory and the file store."""
        if key not in self:
            raise KeyError(key)
        with self._lock:
            try:
                del self._memoryStore[key]
            except KeyError:
                pass
            try:
                del self._fileStore[key]
            except KeyError:
                pass

    def __contains__(self, key):
        """Check whether the session store has a given key."""
        # First try to find the session in the memory store without locking,
        # for efficiency.  Only if that fails do we acquire the lock and
        # look in the file store.
        if key in self._memoryStore:
            return True
        with self._lock:
            return key in self._memoryStore or key in self._fileStore

    def __iter__(self):
        """Return an iterator over the stored session keys."""
        # since we must be consistent, we cannot chain the iterators
        return iter(self.keys())

    def keys(self):
        """Return a list with all keys of all the stored sessions."""
        with self._lock:
            return self._memoryStore.keys() + self._fileStore.keys()

    def clear(self):
        """Clear the session store in memory and remove all session files."""
        with self._lock:
            self._memoryStore.clear()
            self._fileStore.clear()

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
            try:
                return self._memoryStore.pop(key)
            except Exception:
                if default is NoDefault:
                    return self._fileStore.pop(key)
                return self._fileStore.pop(key, default)

    def moveToMemory(self, key):
        """Move the value for a session from file to memory."""
        with self._lock:
            if debug:
                print(f">> Moving {key} to Memory")
            self._memoryStore[key] = self._fileStore.pop(key)

    def moveToFile(self, key):
        """Move the value for a session from memory to file."""
        with self._lock:
            if debug:
                print(f">> Moving {key} to File")
            self._fileStore[key] = self._memoryStore.pop(key)

    def setEncoderDecoder(self, encoder, decoder):
        """Set the serializer and deserializer for the store."""
        SessionStore.setEncoderDecoder(self, encoder, decoder)
        self._fileStore.setEncoderDecoder(encoder, decoder)

    # endregion Access

    # region Application support

    def storeSession(self, session):
        """Save potentially changed session in the store."""
        if self._alwaysSave or session.isDirty():
            key = session.identifier()
            with self._lock:
                if key in self:
                    if key in self._memoryStore:
                        if self._memoryStore[key] is not session:
                            self._memoryStore[key] = session
                    else:
                        self._fileStore[key] = session
                else:
                    self[key] = session

    def storeAllSessions(self):
        """Permanently save all sessions in the store."""
        with self._lock:
            for key in self._memoryStore.keys():
                self.moveToFile(key)

    def cleanStaleSessions(self, task=None):
        """Clean stale sessions.

        Called by the Application to tell this store to clean out all sessions
        that have exceeded their lifetime.
        We want to have their native class functions handle it, though.

        Ideally, intervalSweep would be run more often than the
        cleanStaleSessions functions for the actual stores.
        This may need to wait until we get the TaskKit in place, though.

        The problem is the FileStore.cleanStaleSessions() method can take a
        while to run. So here, we only run the file sweep every fourth time.
        """
        if debug:
            print("Session Sweep started")
        try:
            if self._fileSweepCount == 0:
                self._fileStore.cleanStaleSessions(task)
            self._memoryStore.cleanStaleSessions(task)
        except KeyError:
            pass
        if self._fileSweepCount < 4:
            self._fileSweepCount += 1
        else:
            self._fileSweepCount = 0
        # Now move sessions from memory to file as necessary:
        self.intervalSweep()
        # It's OK for a session to be moved from memory to file or vice versa
        # in between the time we get the keys and the time we actually ask
        # for the session's access time. It may take a while for the fileStore
        # sweep to get completed.

    def intervalSweep(self):
        """The session sweeper interval function.

        The interval function moves sessions from memory to file
        and can be run more often than the full cleanStaleSessions function.
        """
        if debug:
            print("Starting interval Sweep at", time.ctime(time.time()))
            print("Memory Sessions:", len(self._memoryStore),
                  "FileSessions:", len(self._fileStore))
            print("maxDynamicMemorySessions =", self._maxDynamicMemorySessions)
            print("moveToFileInterval =", self._moveToFileInterval)

        now = time.time()

        moveToFileTime = now - self._moveToFileInterval
        keys = []
        for key in self._memoryStore.keys():
            try:
                if self._memoryStore[key].lastAccessTime() < moveToFileTime:
                    if self._memoryStore[key].isNew():
                        if debug:
                            print("trashing one-shot session", key)
                    else:
                        keys.append(key)
            except KeyError:
                pass
        for key in keys:
            try:
                self.moveToFile(key)
            except KeyError:
                pass

        if len(self._memoryStore) > self._maxDynamicMemorySessions:
            keys = self.memoryKeysInAccessTimeOrder()
            excess = len(self._memoryStore) - self._maxDynamicMemorySessions
            if debug:
                print(excess, "sessions beyond the limit")
            keys = keys[:excess]
            for key in keys:
                try:
                    self.moveToFile(key)
                except KeyError:
                    pass

        if debug:
            print("Finished interval Sweep at", time.ctime(time.time()))
            print("Memory Sessions:", len(self._memoryStore),
                  "FileSessions:", len(self._fileStore))

    def memoryKeysInAccessTimeOrder(self):
        """Fetch memory store's keys in ascending order of last access time."""
        return [session.identifier() for session in sorted(
            self._memoryStore.values(), key=lambda v: v.lastAccessTime())]

    # endregion Application support
