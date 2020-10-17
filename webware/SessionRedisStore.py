"""Session store using the Redis in-memory data store."""

from pickle import loads, dumps

try:
    import redis  # pylint: disable=import-error
except Exception as e:
    raise ImportError(
        "For using Redis sessions,"
        " redis-py must be installed.") from e

from MiscUtils import NoDefault

from SessionStore import SessionStore

debug = False


class SessionRedisStore(SessionStore):
    """A session store using Redis.

    Stores the sessions in a single Redis store using 'last write wins'
    semantics. This increases fault tolerance and allows server clustering.
    In clustering configurations with concurrent writes for the same
    session(s) the last writer will always overwrite the session.

    The keys are prefixed with a configurable namespace, allowing you to
    store other data in the same Redis system.

    Cleaning/timing out of sessions is performed by Redis itself since
    no single application can know about the existence of all sessions or
    the last access for a given session. Besides it is built in Redis
    functionality. Consequently, correct sizing of Redis is necessary
    to hold all user's session data.

    You need to install the redis client to be able to use this module:
    https://pypi.python.org/pypi/redis
    You also need a Redis server: https://redis.io/

    Contributed by Christoph Zwerschke, August 2016.
    """

    # region Init

    def __init__(self, app):
        SessionStore.__init__(self, app)

        # the list of redis servers
        self._host = app.setting('RedisHost', 'localhost')
        self._port = app.setting('RedisPort', 6379)
        self._db = app.setting('RedisDb', 0)
        self._password = app.setting('RedisPassword', None)

        # timeout in seconds
        self._sessionTimeout = app.setting('SessionTimeout', 180) * 60

        # the redis "namespace" used by our store
        self._namespace = app.setting(
            'RedisNamespace', 'WebwareSession:') or ''

        self._redis = redis.StrictRedis(
            self._host, self._port, self._db, self._password)

    # endregion Init

    # region Access

    def __len__(self):
        """Return the number of sessions in the store."""
        if debug:
            print(">> len()")
        return len(self.keys())

    def __getitem__(self, key):
        """Get a session item, reading it from the store."""
        if debug:
            print(f">> getitem({key})")
        # returns None if key non-existent or no server to contact
        try:
            value = loads(self._redis.get(self.redisKey(key)))
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
                self._redis.setex(
                    self.redisKey(key), self._sessionTimeout, dumps(value, -1))
            except Exception as exc:
                if dirty:
                    value.setDirty()
                # Not able to store the session is a failure
                print(f"Error saving session {key!r} to redis: {exc}")
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
            self._redis.delete(self.redisKey(key))
        except Exception as exc:
            # Not able to delete the session is a failure
            print(f"Error deleting session {key!r} from redis: {exc}")
            self.application().handleException()

    def __contains__(self, key):
        """Check whether the session store has a given key."""
        if debug:
            print(f">> contains({key})")
        try:
            return self._redis.exists(self.redisKey(key))
        except Exception as exc:
            # Not able to check the session is a failure
            print(f"Error checking session {key!r} from redis: {exc}")
            self.application().handleException()

    def __iter__(self):
        """Return an iterator over the stored session keys."""
        if debug:
            print(">> iter()")
        return self.keys().__iter__()

    def keys(self):
        """Return a list with the keys of all the stored sessions."""
        if debug:
            print(">> keys()")
        try:
            if self._namespace:
                n = len(self._namespace)
                return [k[n:] for k in self._redis.keys(self.redisKey('*'))]
            return self._redis.keys(self.redisKey('*'))
        except Exception as exc:
            # Not able to get the keys is a failure
            print("Error checking sessions from redis:", exc)
            self.application().handleException()

    def clear(self):
        """Clear the session store, removing all of its items."""
        if debug:
            print(">> clear()")
        try:
            if self._namespace:
                self._redis.delete(*self._redis.keys(self.redisKey('*')))
            else:
                self._redis.flushdb()
        except Exception as exc:
            # Not able to clear the store is a failure
            print("Error clearing sessions from redis:", exc)
            self.application().handleException()

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
        This closes the connections to the Redis server.
        """
        if debug:
            print(">> storeAllSessions()")
        try:
            self._redis.connection_pool.disconnect()
        except Exception as exc:
            print("Not able to disconnect from redis:", exc)

    def cleanStaleSessions(self, _task=None):
        """Clean stale sessions.

        Redis does this on its own, so we do nothing here.
        """
        if debug:
            print(">> cleanStaleSessions()")

    # endregion Application support

    # region Auxiliary methods

    def redisKey(self, key):
        """Create the real key with namespace to be used with Redis."""
        return self._namespace + key

    # endregion Auxiliary methods
