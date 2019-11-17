"""The abstract UserManager class."""

from MiscUtils import AbstractError, NoDefault
from .User import User


class UserManager:
    """The base class for all user manager classes.

    A UserManager manages a set of users including authentication,
    indexing and persistence. Keep in mind that UserManager is abstract;
    you must always use a concrete subclasses like UserManagerToFile
    (but please read the rest of this docstring).

    You can create a user through the manager (preferred)::

        user = manager.createUser(name, password)

    Or directly through the user class::

        user = RoleUser(manager, name, password)
        manager.addUser(user)

    The manager tracks users by whether or not they are "active"
    (e.g., logged in) and indexes them by:

      * user serial number
      * external user id
      * user name

    These methods provide access to the users by these keys::

        def userForSerialNum(self, serialNum, default=NoDefault)
        def userForExternalId(self, extId, default=NoDefault)
        def userForName(self, name, default=NoDefault)

    UserManager provides convenient methods for iterating through the
    various users. Each method returns an object that can be used in a
    for loop and asked for its len()::

        def users(self)
        def activeUsers(self)
        def inactiveUsers(self)

    You can authenticate a user by passing the user object and attempted
    password to login(). If the authentication is successful, then login()
    returns the User, otherwise it returns None::

        user = mgr.userForExternalId(externalId)
        if mgr.login(user, password):
            self.doSomething()

    As a convenience, you can authenticate by passing the serialNum,
    externalId or name of the user::

        def loginSerialNum(self, serialNum, password):
        def loginExternalId(self, externalId, password):
        def loginName(self, userName, password):

    The user will automatically log out after a period of inactivity
    (see below), or you can make it happen with::

        def logout(self, user):

    There are three user states that are important to the manager:

      * modified
      * cached
      * authenticated or "active"

    A modified user is one whose data has changed and eventually requires
    storage to a persistent location. A cached user is a user whose data
    resides in memory (regardless of the other states). An active user
    has been authenticated (e.g., their username and password were checked)
    and has not yet logged out or timed out.

    The manager keeps three timeouts, expressed in minutes, to:

      * save modified users after a period of time following the first
        unsaved modification
      * push users out of memory after a period of inactivity
      * deactivate (e.g., log out) users after a period of inactivity

    The methods for managing these values deal with the timeouts as
    number-of-minutes. The default values and the methods are:

      * 20  modifiedUserTimeout()  setModifiedUserTimeout()
      * 20  cachedUserTimeout()    setCachedUserTimeout()
      * 20  activeUserTimeout()    setActiveUserTimeout()

    Subclasses of UserManager provide persistence such as to the file
    system or a MiddleKit store. Subclasses must implement all methods
    that raise AbstractErrors. Subclasses typically override (while still
    invoking super) addUser().

    Subclasses should ensure "uniqueness" of users. For example, invoking
    any of the userForSomething() methods repeatedly should always return
    the same user instance for a given key. Without uniqueness, consistency
    issues could arise with users that are modified.

    Please read the method docstrings and other class documentation to
    fully understand UserKit.
    """

    # region Init

    def __init__(self, userClass=None):
        if userClass is None:
            self._userClass = None
        else:
            self.setUserClass(userClass)
        self._cachedUsers = []
        self._cachedUsersBySerialNum = {}
        self.setModifiedUserTimeout(20)
        self.setCachedUserTimeout(20)
        self.setActiveUserTimeout(20)
        self._numActive = 0

    def shutDown(self):
        """Perform any tasks necessary to shut down the user manager.

        Subclasses may override and must invoke super as their *last* step.
        """
        # base method does nothing

    # endregion Init

    # region Settings

    def userClass(self):
        """Return the userClass, which is used by createUser.

        The default value is UserKit.User.User.
        """
        if self._userClass is None:
            self.setUserClass(User)
        return self._userClass

    def setUserClass(self, userClass):
        """Set the userClass, which cannot be None and must inherit from User.

        See also: userClass().
        """
        if not issubclass(userClass, User):
            raise TypeError(f'{userClass} is not a User class')
        self._userClass = userClass

    def modifiedUserTimeout(self):
        return self._modifiedUserTimeout

    def setModifiedUserTimeout(self, value):
        self._modifiedUserTimeout = value

    def cachedUserTimeout(self):
        return self._cachedUserTimeout

    def setCachedUserTimeout(self, value):
        self._cachedUserTimeout = value

    def activeUserTimeout(self):
        return self._activeUserTimeout

    def setActiveUserTimeout(self, value):
        self._activeUserTimeout = value

    # endregion Settings

    # region Basic user access

    def createUser(self, name, password, userClass=None):
        """Return a newly created user that is added to the manager.

        If userClass is not specified, the manager's default user class
        is instantiated. This not imply that the user is logged in.
        This method invokes self.addUser().

        See also: userClass(), setUserClass()
        """
        if userClass is None:
            userClass = self.userClass()
        user = userClass(manager=self, name=name, password=password)
        self.addUser(user)
        return user

    def addUser(self, user):
        if not isinstance(user, User):
            raise TypeError(f'{user} is not a User object')
        self._cachedUsers.append(user)
        if user.serialNum() in self._cachedUsersBySerialNum:
            raise KeyError('a user with this number already exists')
        self._cachedUsersBySerialNum[user.serialNum()] = user

    def userForSerialNum(self, serialNum, default=NoDefault):
        """Return the user with the given serialNum.

        The user record is pulled into memory if needed.
        """
        raise AbstractError(self.__class__)

    def userForExternalId(self, externalId, default=NoDefault):
        """Return the user with the given external id.

        The user record is pulled into memory if needed.
        """
        raise AbstractError(self.__class__)

    def userForName(self, name, default=NoDefault):
        """Return the user with the given name.

        The user record is pulled into memory if needed.
        """
        raise AbstractError(self.__class__)

    def users(self):
        """Return a list of all users (regardless of login status)."""
        raise AbstractError(self.__class__)

    def numActiveUsers(self):
        """Return the number of active users (e.g. the logged in users)."""
        return self._numActive

    def activeUsers(self):
        """Return a list of all active users."""
        raise AbstractError(self.__class__)

    def inactiveUsers(self):
        raise AbstractError(self.__class__)

    # endregion Basic user access

    # region Logging in and out

    def login(self, user, password):
        """Return the user if login is successful, otherwise return None."""
        if not isinstance(user, User):
            raise TypeError(f'{user} is not a User object')
        result = user.login(password, fromMgr=True)
        if result:
            self._numActive += 1
        return result

    def logout(self, user):
        if not isinstance(user, User):
            raise TypeError(f'{user} is not a User object')
        user.logout(fromMgr=True)
        self._numActive -= 1

    def loginSerialNum(self, serialNum, password):
        # pylint: disable=assignment-from-no-return
        user = self.userForSerialNum(serialNum, None)
        if user:
            return self.login(user, password)
        return None

    def loginExternalId(self, externalId, password):
        # pylint: disable=assignment-from-no-return
        user = self.userForExternalId(externalId, None)
        if user:
            return self.login(user, password)
        return None

    def loginName(self, userName, password):
        # pylint: disable=assignment-from-no-return
        user = self.userForName(userName, None)
        if user:
            return self.login(user, password)
        return None

    # endregion Logging in and out

    # region Cached

    def clearCache(self):
        """Clear the cache of the manager.

        Use with extreme caution. If your program maintains a reference
        to a user object, but the manager loads in a new copy later on,
        then consistency problems could occur.

        The most popular use of this method is in the regression test suite.
        """
        self._cachedUsers = []
        self._cachedUsersBySerialNum = {}

    # endregion Cached
