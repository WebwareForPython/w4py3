"""Mock Webware Session class."""

from time import time


class Session:
    """Mock session."""

    _lastExpired = None

    def __init__(self, identifier=7, value=None):
        self._identifier = f'foo-{identifier}'
        self._data = dict(bar=value or identifier * 6)
        self._expired = self._dirty = False
        self._timeout = 1800
        self._lastAccessTime = time() - identifier * 400
        self._isNew = True

    def identifier(self):
        return self._identifier

    def expiring(self):
        self._expired = True
        Session._lastExpired = self._identifier

    def isDirty(self):
        return self._dirty

    def setDirty(self, dirty=True):
        self._dirty = dirty

    def isExpired(self):
        return self._expired

    def timeout(self):
        return self._timeout

    def data(self):
        return self._data

    def bar(self):
        return self._data.get('bar')

    def setBar(self, value):
        self._isNew = False
        self._data['bar'] = value

    def isNew(self):
        return self._isNew

    def lastAccessTime(self):
        return self._lastAccessTime
