"""Universal error class."""


class Error(dict):
    """Universal error class.

    An error is a dictionary-like object, containing a specific
    user-readable error message and an object associated with it.
    Since Error inherits dict, other informative values can be arbitrarily
    attached to errors. For this reason, subclassing Error is rare.

    Example::

        err = Error(user, 'Invalid password.')
        err['time'] = time.time()
        err['attempts'] = attempts

    The object and message can be accessed via methods::

        print(err.object())
        print(err.message())

    When creating errors, you can pass None for both object and message.
    You can also pass additional values, which are then included in the error::

        >>> err = Error(None, 'Too bad.', timestamp=time.time())
        >>> err.keys()
        ['timestamp']

    Or include the values as a dictionary, instead of keyword arguments::

        >>> info = {'timestamp': time.time()}
        >>> err = Error(None, 'Too bad.', info)

    Or you could even do both if you needed to.
    """

    def __init__(self, obj, message, valueDict=None, **valueArgs):
        """Initialize the error.

        Takes the object the error occurred for, and the user-readable
        error message. The message should be self sufficient such that
        if printed by itself, the user would understand it.
        """
        dict.__init__(self)
        self._object = obj
        self._message = message
        if valueDict:
            self.update(valueDict)
        self.update(valueArgs)

    def object(self):
        """Get the object the error occurred for."""
        return self._object

    def message(self):
        """Get the user-readable error message."""
        return self._message

    def __repr__(self):
        return (f'ERROR(object={self._object!r};'
                f' message={self._message!r}; data={dict(self)!r})')

    def __str__(self):
        return f'ERROR: {self._message}'

    def __bool__(self):
        return True
