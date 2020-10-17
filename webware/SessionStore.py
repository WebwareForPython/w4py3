"""A general session store."""

from pickle import load, dump, HIGHEST_PROTOCOL as maxPickleProtocol
from warnings import warn

from time import time

from MiscUtils import AbstractError


def dumpWithHighestProtocol(obj, f):
    """Same as pickle.dump, but by default with the highest protocol."""
    return dump(obj, f, maxPickleProtocol)


class SessionStore:
    """A general session store.

    SessionStores are dictionary-like objects used by Application to
    store session state. This class is abstract and it's up to the
    concrete subclass to implement several key methods that determine
    how sessions are stored (such as in memory, on disk or in a
    database). We assume that session keys are always strings.

    Subclasses often encode sessions for storage somewhere. In light
    of that, this class also defines methods encoder(), decoder() and
    setEncoderDecoder(). The encoder and decoder default to the load()
    and dump() functions of the pickle module. However, using the
    setEncoderDecoder() method, you can use the functions from marshal
    (if appropriate) or your own encoding scheme. Subclasses should use
    encoder() and decoder() (and not pickle.load() and pickle.dump()).

    Subclasses may rely on the attribute self._app to point to the
    application.

    Subclasses should be named SessionFooStore since Application
    expects "Foo" to appear for the "SessionStore" setting and
    automatically prepends Session and appends Store. Currently, you
    will also need to add another import statement in Application.py.
    Search for SessionStore and you'll find the place.

    TO DO

      * Should there be a check-in/check-out strategy for sessions to
        prevent concurrent requests on the same session? If so, that can
        probably be done at this level (as opposed to pushing the burden
        on various subclasses).
    """

    # region Init

    def __init__(self, app):
        """Initialize the session store.

        Subclasses must invoke super.
        """
        self._app = app
        self._alwaysSave = app._alwaysSaveSessions
        self._retain = app._retainSessions
        self._encoder = dumpWithHighestProtocol
        self._decoder = load

    # endregion Init

    # region Access

    def application(self):
        """Return the application owning the session store."""
        return self._app

    # endregion Access

    # region Dictionary-style access

    def __len__(self):
        """Return the number of sessions in the store.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def __getitem__(self, key):
        """Get a session item from the store.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def __setitem__(self, key, value):
        """Set a session item, saving it to the store.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def __delitem__(self, key):
        """Delete a session item from the store.

        Subclasses are responsible for expiring the session as well.
        Something along the lines of:
            session = self[key]
            if not session.isExpired():
                session.expiring()
        """
        raise AbstractError(self.__class__)

    def __contains__(self, key):
        """Check whether the session store has a given key.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def __iter__(self):
        """Return an iterator over the stored session keys.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def has_key(self, key):
        """Check whether the session store has a given key."""
        warn("has_key is deprecated, please us 'in' instead.",
             DeprecationWarning, stacklevel=2)
        return key in self

    def keys(self):
        """Return a list with the keys of all the stored sessions.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def iterkeys(self):
        """Return an iterator over the stored session keys."""
        return iter(self)

    def clear(self):
        """Clear the session store, removing all of its items.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def setdefault(self, key, default=None):
        """Return value if key available, else default (also setting it).

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def pop(self, key, default=None):
        """Return value if key available, else default (also remove key).

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    # endregion Dictionary-style access

    # region Application support

    def storeSession(self, session):
        """Save potentially changed session in the store.

        Used at the end of transactions.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def storeAllSessions(self):
        """Permanently save all sessions in the store.

        Used when the application server is shut down.

        Subclasses must implement this method.
        """
        raise AbstractError(self.__class__)

    def cleanStaleSessions(self, _task=None):
        """Clean stale sessions.

        Called by the Application to tell this store to clean out all
        sessions that have exceeded their lifetime.
        """
        curTime = time()
        keys = []
        for key in self.keys():
            try:
                session = self[key]
            except KeyError:
                pass  # session was already deleted by some other thread
            else:
                try:
                    timeout = session.timeout()
                    if timeout is not None and (
                            timeout == 0 or
                            curTime >= session.lastAccessTime() + timeout):
                        keys.append(key)
                except AttributeError as e:
                    raise ValueError(
                        f'Not a Session object: {session!r}') from e
        for key in keys:
            try:
                del self[key]
            except KeyError:
                pass  # already deleted by some other thread

    # endregion Application support

    # region Convenience methods

    def get(self, key, default=None):
        """Return value if key available, else return the default."""
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        """Return a list with the (key, value) pairs for all sessions."""
        return list(self.iteritems())

    def values(self):
        """Return a list with the values of all stored sessions."""
        return list(self.itervalues())

    def iteritems(self):
        """Return an iterator over the (key, value) pairs for all sessions."""
        for key in self.keys():
            # since the size of the store might change during iteration,
            # we iterate over the list of keys, not the store itself
            try:
                yield key, self[key]
            except KeyError:
                # since we aren't using a lock here, some keys
                # could be already deleted again during this loop
                pass

    def itervalues(self):
        """Return an iterator over the stored values of all sessions."""
        for key in self.keys():
            try:
                yield self[key]
            except KeyError:
                pass

    # endregion Convenience methods

    # region Encoder/decoder

    def encoder(self):
        """Return the value serializer for the store."""
        return self._encoder

    def decoder(self):
        """Return the value deserializer for the store."""
        return self._decoder

    def setEncoderDecoder(self, encoder, decoder):
        """Set the serializer and deserializer for the store."""
        self._encoder = encoder
        self._decoder = decoder

    # endregion Encoder/decoder

    # region As a string

    def __repr__(self):
        """Return string representation of the store like a dictionary."""
        return repr(dict(self.items()))

    # endregion As a string
