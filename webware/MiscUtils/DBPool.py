"""DBPool.py

Implements a pool of cached connections to a database for any DB-API 2
compliant database module. This should result in a speedup for persistent
applications like Webware. The pool of connections is threadsafe regardless
of whether the used DB-API 2 general has a threadsafety of 1 or 2.

For more information on the DB-API 2 specification, see `PEP 249`_.

.. _PEP 249: https://www.python.org/dev/peps/pep-0249/

The idea behind DBPool is that it's completely seamless, so once you have
established your connection, use it just as you would any other DB-API 2
compliant module. For example::

    import pgdb  # import used DB-API 2 module
    from MiscUtils.DBPool import DBPool
    dbpool = DBPool(pgdb, 5, host=..., database=..., user=..., ...)
    db = dbpool.connection()

Now use "db" exactly as if it were a pgdb connection. It's really
just a proxy class.

db.close() will return the connection to the pool, not actually
close it. This is so your existing code works nicely.

DBPool is actually intended to be a demonstration of concept not to be
used in a productive environment. It is really a very simple solution with
several drawbacks. For instance, pooled database connections which have
become invalid are not automatically recovered. For a more sophisticated
solution, please have a look at the DBUtils_ package.

.. _DBUtils: https://webwareforpython.github.io/dbutils/


CREDIT

  * Contributed by Dan Green.
  * Thread safety bug found by Tom Schwaller.
  * Fixes by Geoff Talvola (thread safety in `_threadsafe_get_connection()`).
  * Clean up by Chuck Esterbrook.
  * Fix unthreadsafe functions which were leaking, Jay Love.
  * Eli Green's webware-discuss comments were lifted for additional docs.
  * Coding and comment clean-up by Christoph Zwerschke.
"""


class DBPoolError(Exception):
    """General database pooling error."""


class NotSupportedError(DBPoolError):
    """Missing support from database module error."""


class PooledConnection:
    """A wrapper for database connections to help with DBPool.

    You don't normally deal with this class directly,
    but use DBPool to get new connections.
    """

    def __init__(self, pool, con):
        self._con = con
        self._pool = pool

    def close(self):
        """Close the pooled connection."""
        # Instead of actually closing the connection,
        # return it to the pool so it can be reused.
        if self._con is not None:
            self._pool.returnConnection(self._con)
            self._con = None

    def __getattr__(self, name):
        # All other members are the same.
        return getattr(self._con, name)

    def __del__(self):
        self.close()


class DBPool:

    def __init__(self, dbapi, maxconnections, *args, **kwargs):
        """Set up the database connection pool.

        `dbapi`:
          the DB-API 2 compliant module you want to use
        `maxconnections`:
          the number of connections cached in the pool
        `args`, `kwargs`:
          the parameters that shall be used to establish the database
          connections using ``dbapi.connect()``
        """
        try:
            threadsafety = dbapi.threadsafety
        except Exception:
            threadsafety = None
        if threadsafety == 0:
            raise NotSupportedError(
                "Database module does not support any level of threading.")
        if dbapi.threadsafety == 1:
            # If there is no connection level safety, build
            # the pool using the synchronized queue class
            # that implements all the required locking semantics.
            from queue import Queue
            self._queue = Queue(maxconnections)  # create the queue
            self.connection = self._unthreadsafeGetConnection
            self.addConnection = self._unthreadsafeAddConnection
            self.returnConnection = self._unthreadsafeReturnConnection
        elif dbapi.threadsafety in (2, 3):
            # If there is connection level safety, implement the
            # pool with an ordinary list used as a circular buffer.
            # We only need a minimum of locking in this case.
            from threading import Lock
            self._lock = Lock()  # create a lock object to be used later
            self._nextCon = 0  # the index of the next connection to be used
            self._connections = []  # the list of connections
            self.connection = self._threadsafeGetConnection
            self.addConnection = self._threadsafeAddConnection
            self.returnConnection = self._threadsafeReturnConnection
        else:
            raise NotSupportedError(
                'Database module threading support cannot be determined.')
        # Establish all database connections (it would be better to
        # only establish a part of them now, and the rest on demand).
        for _count in range(maxconnections):
            self.addConnection(dbapi.connect(*args, **kwargs))

    # The following functions are used with DB-API 2 modules
    # that do not have connection level threadsafety, like PyGreSQL.
    # However, the module must be threadsafe at the module level.
    # Note: threadsafe/unthreadsafe refers to the DB-API 2 module,
    # not to this class which should be threadsafe in any case.

    def _unthreadsafeGetConnection(self):
        """Get a connection from the pool."""
        return PooledConnection(self, self._queue.get())

    def _unthreadsafeAddConnection(self, con):
        """Add a connection to the pool."""
        self._queue.put(con)

    def _unthreadsafeReturnConnection(self, con):
        """Return a connection to the pool.

        In this case, the connections need to be put
        back into the queue after they have been used.
        This is done automatically when the connection is closed
        and should never be called explicitly outside of this module.
        """
        self._unthreadsafeAddConnection(con)

    # The following functions are used with DB-API 2 modules
    # that are threadsafe at the connection level, like psycopg.
    # Note: In this case, connections are shared between threads.
    # This may lead to problems if you use transactions.

    def _threadsafeGetConnection(self):
        """Get a connection from the pool."""
        with self._lock:
            nextCon = self._nextCon
            con = PooledConnection(self, self._connections[nextCon])
            nextCon += 1
            if nextCon >= len(self._connections):
                nextCon = 0
            self._nextCon = nextCon
            return con

    def _threadsafeAddConnection(self, con):
        """"Add a connection to the pool."""
        self._connections.append(con)

    def _threadsafeReturnConnection(self, con):
        """Return a connection to the pool.

        In this case, the connections always stay in the pool,
        so there is no need to do anything here.
        """
        # does nothing
