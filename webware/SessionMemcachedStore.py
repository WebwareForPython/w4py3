"""Session store using the Memcached memory object caching system."""

from warnings import warn
from pickle import HIGHEST_PROTOCOL as maxPickleProtocol

try:
    import memcache  # pylint: disable=import-error
except Exception as e:
    raise ImportError(
        "For using Memcached sessions,"
        " python-memcached must be installed.") from e

from MiscUtils import NoDefault

from SessionStore import SessionStore

debug = False


class SessionMemcachedStore(SessionStore):
    """A session store using Memcached.

    Stores the sessions in a single Memcached store using 'last write wins'
    semantics. This increases fault tolerance and allows server clustering.
    In clustering configurations with concurrent writes for the same
    session(s) the last writer will always overwrite the session.

    The keys are prefixed with a configurable namespace, allowing you to
    store other data in the same Memcached system.

    Cleaning/timing out of sessions is performed by Memcached itself since
    no single application can know about the existence of all sessions or
    the last access for a given session. Besides it is built in Memcached
    functionality. Consequently, correct sizing of Memcached is necessary
    to hold all user's session data.

    Due to the way Memcached works, methods requiring access to the keys
    or for clearing the store do not work. You can configure whether you
    want to ignore such calls or raise an error in this case. By default,
    you will get a warning. It would be possible to emulate these functions
    by storing additional data in the memcache, such as a namespace counter
    or the number or even the full list of keys. However, if you are using
    more than one application instance, this would require fetching that data
    every time, since we cannot know whether another instance changed it.
    So we refrained from doing such sophisticated trickery and instead kept
    the implementation intentionally very simple and fast.

    You need to install python-memcached to be able to use this module:
    https://www.tummy.com/software/python-memcached/
    You also need a Memcached server: https://memcached.org/

    Contributed by Steve Schwarz, March 2010.
    Small improvements by Christoph Zwerschke, April 2010.
    """

    # region Init

    def __init__(self, app):
        SessionStore.__init__(self, app)

        # the list of memcached servers
        self._servers = app.setting('MemcachedServers', ['localhost:11211'])

        # timeout in seconds
        self._sessionTimeout = app.setting('SessionTimeout', 180) * 60

        # the memcached "namespace" used by our store
        # you can add an integer counter for expiration
        self._namespace = app.setting(
            'MemcachedNamespace', 'WebwareSession:') or ''

        # when trying to iterate over the Memcached store,
        # you can trigger an error or a warning
        self._onIteration = app.setting('MemcachedOnIteration', 'Warning')

        self._client = memcache.Client(
            self._servers, debug=debug, pickleProtocol=maxPickleProtocol)

    # endregion Init

    # region Access

    def __len__(self):
        """Return the number of sessions in the store.

        Not supported by Memcached (see FAQ for explanation).
        """
        if debug:
            print(">> len()")
        return len(self.keys())

    def __getitem__(self, key):
        """Get a session item, reading it from the store."""
        if debug:
            print(f">> getitem({key})")
        # returns None if key non-existent or no server to contact
        try:
            value = self._client.get(self.mcKey(key))
        except Exception:
            value = None
        if value is None:
            # SessionStore expects KeyError when no result
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        """Set a session item, writing it to the store."""
        if debug:
            print(f">> setitem({key}, {value})")
        dirty = value.isDirty()
        if self._alwaysSave or dirty:
            if dirty:
                value.setDirty(False)
            try:
                if not self._client.set(
                        self.mcKey(key), value, time=self._sessionTimeout):
                    raise ValueError("Setting value in the memcache failed.")
            except Exception as exc:
                if dirty:
                    value.setDirty()
                # Not able to store the session is a failure
                print(f"Error saving session {key!r} to memcache: {exc}")
                self.application().handleException()

    def __delitem__(self, key):
        """Delete a session item from the store.

        Note that in contracts with SessionFileStore,
        not finding a key to delete isn't a KeyError.
        """
        if debug:
            print(f">> delitem({key})")
        session = self[key]
        if not session.isExpired():
            session.expiring()
        try:
            if not self._client.delete(self.mcKey(key)):
                raise ValueError("Deleting value from the memcache failed.")
        except Exception as exc:
            # Not able to delete the session is a failure
            print(f"Error deleting session {key!r} from memcache: {exc}")
            self.application().handleException()

    def __contains__(self, key):
        """Check whether the session store has a given key."""
        if debug:
            print(f">> contains({key})")
        try:
            return self._client.get(self.mcKey(key)) is not None
        except Exception:
            return False

    def __iter__(self):
        """Return an iterator over the stored session keys.

        Not supported by Memcached (see FAQ for explanation).
        """
        if debug:
            print(">> iter()")
        onIteration = self._onIteration
        if onIteration:
            err = 'Memcached does not support iteration.'
            if onIteration == 'Error':
                raise NotImplementedError(err)
            warn(err)
        return iter([])

    def keys(self):
        """Return a list with the keys of all the stored sessions.

        Not supported by Memcached (see FAQ for explanation).
        """
        if debug:
            print(">> keys()")
        return list(iter(self))

    def clear(self):
        """Clear the session store, removing all of its items.

        Not supported by Memcached. We could emulate this by incrementing
        an additional namespace counter, but then we would need to fetch
        the current counter from the memcache before every access in order
        to keep different application instances in sync.
        """
        if debug:
            print(">> clear()")
        if self._onIteration:
            err = 'Memcached does not support clearing the store.'
            if self._onIteration == 'Error':
                raise NotImplementedError(err)
            warn(err)

    def setdefault(self, key, default=None):
        """Return value if key available, else default (also setting it)."""
        if debug:
            print(f">> setdefault({key}, {default})")
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def pop(self, key, default=NoDefault):
        """Return value if key available, else default (also remove key)."""
        if debug:
            print(f">> pop({key}, {default})")
        if default is NoDefault:
            value = self[key]
            del self[key]
            return value
        try:
            value = self[key]
        except KeyError:
            return default
        else:
            del self[key]
            return value

    # endregion Access

    # region Application support

    def storeSession(self, session):
        """Save potentially changed session in the store."""
        if debug:
            print(f">> storeSession({session})")
        self[session.identifier()] = session

    def storeAllSessions(self):
        """Permanently save all sessions in the store.

        Should be used (only) when the application server is shut down.
        This closes the connection to the Memcached servers.
        """
        if debug:
            print(">> storeAllSessions()")
        self._client.disconnect_all()

    def cleanStaleSessions(self, _task=None):
        """Clean stale sessions.

        Memcached does this on its own, so we do nothing here.
        """
        if debug:
            print(">> cleanStaleSessions()")

    # endregion Application support

    # region Auxiliary methods

    def mcKey(self, key):
        """Create the real key with namespace to be used with Memcached."""
        return self._namespace + key

    # endregion Auxiliary methods
