"""The basic User class."""

from time import time

from MiscUtils.Funcs import uniqueId


class User:
    """The base class for a UserKit User."""

    # region Init

    def __init__(self, manager=None, name=None, password=None):
        self._creationTime = time()

        self._manager = None
        self._name = None
        self._password = None
        self._isActive = False
        self._externalId = None

        if name is not None:
            self.setName(name)
        if manager is not None:
            self.setManager(manager)
        if password is not None:
            self.setPassword(password)

    def __str__(self):
        return self.name()

    # endregion Init

    # region Attributes

    def manager(self):
        return self._manager

    def setManager(self, manager):
        """Set the manager, which can only be done once."""
        if self._manager is not None:
            raise KeyError('Manager has already been set')
        from .UserManager import UserManager
        if not isinstance(manager, UserManager):
            raise TypeError(f'{manager} is not a UserManager object')
        if manager.userForName(self.name(), None) is not None:
            raise KeyError(f'There is already a user named {self._name!r}.')
        self._manager = manager

    def serialNum(self):
        return self._serialNum

    def setSerialNum(self, serialNum):
        self._serialNum = serialNum

    def externalId(self):
        if self._externalId is None:
            self._externalId = uniqueId(self)
        return self._externalId

    def name(self):
        return self._name

    def setName(self, name):
        """Set the name, which can only be done once."""
        if self._name is not None:
            raise KeyError('name has already been set')
        self._name = name

    def password(self):
        return self._password

    def setPassword(self, password):
        self._password = password

    def isActive(self):
        return self._isActive

    def creationTime(self):
        return self._creationTime

    def lastAccessTime(self):
        return self._lastAccessTime

    def lastLoginTime(self):
        return self._lastLoginTime

    # endregion Attributes

    # region Log in and out

    def login(self, password, fromMgr=0):
        """Return self if the login is successful and None otherwise."""
        if not fromMgr:
            # Our manager needs to know about this.
            # So make sure we go through him.
            return self.manager().login(self, password)
        if password == self.password():
            self._isActive = True
            self._lastLoginTime = self._lastAccessTime = time()
            return self
        if self._isActive:
            # We were already logged in, but we tried again and
            # this time it failed. Logout:
            self.logout()
        return None

    def logout(self, fromMgr=False):
        if fromMgr:
            self._isActive = False
            self._lastLogoutTime = time()
        else:
            # Our manager needs to know about this.
            # So make sure we go through him.
            self.manager().logout(self)

    # region Log in and out

    # region Notifications

    def wasAccessed(self):
        self._lastAccessTime = time()

    # endregion Notifications
