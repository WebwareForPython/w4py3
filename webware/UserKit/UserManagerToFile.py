"""The UserManagerToFile class."""

import os

from glob import glob
from pickle import load, dump

from MiscUtils import NoDefault
from MiscUtils.MixIn import MixIn

from .User import User
from .UserManager import UserManager


class UserManagerToFile(UserManager):
    """User manager storing user data in the file system.

    When using this user manager, make sure you invoke setUserDir()
    and that this directory is writeable by your application.
    It will contain one file per user with the user's serial number
    as the main filename and an extension of '.user'.

    The default user directory is the current working directory,
    but relying on the current directory is often a bad practice.
    """

    # region Init

    def __init__(self, userClass=None):
        UserManager.__init__(self, userClass=None)
        self.setEncoderDecoder(dump, load)
        self.setUserDir(os.getcwd())
        self.initNextSerialNum()

    def initNextSerialNum(self):
        if os.path.exists(self._userDir):
            serialNums = self.scanSerialNums()
            if serialNums:
                self._nextSerialNum = max(serialNums) + 1
            else:
                self._nextSerialNum = 1
        else:
            self._nextSerialNum = 1

    # endregion Init

    # region File storage specifics

    def userDir(self):
        return self._userDir

    def setUserDir(self, userDir):
        """Set the directory where user information is stored.

        You should strongly consider invoking initNextSerialNum() afterwards.
        """
        self._userDir = userDir

    def loadUser(self, serialNum, default=NoDefault):
        """Load the user with the given serial number from disk.

        If there is no such user, a KeyError will be raised unless
        a default value was passed, in which case that value is returned.
        """
        filename = f'{serialNum}.user'
        filename = os.path.join(self.userDir(), filename)
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                user = self.decoder()(f)
            self._cachedUsers.append(user)
            self._cachedUsersBySerialNum[serialNum] = user
            return user
        if default is NoDefault:
            raise KeyError(serialNum)
        return default

    def scanSerialNums(self):
        """Return a list of all the serial numbers of users found on disk.

        Serial numbers are always integers.
        """
        return [
            int(os.path.basename(num[:-5]))
            for num in glob(os.path.join(self.userDir(), '*.user'))]

    # endregion File storage specifics

    # region UserManager customizations

    def setUserClass(self, userClass):
        """Overridden to mix in UserMixIn to the class that is passed in."""
        MixIn(userClass, UserMixIn)
        UserManager.setUserClass(self, userClass)

    # endregion UserManager customizations

    # region UserManager concrete methods

    def nextSerialNum(self):
        result = self._nextSerialNum
        self._nextSerialNum += 1
        return result

    def addUser(self, user):
        if not isinstance(user, User):
            raise TypeError(f'{user} is not a User object')
        user.setSerialNum(self.nextSerialNum())
        user.externalId()  # set unique id
        UserManager.addUser(self, user)
        user.save()

    def userForSerialNum(self, serialNum, default=NoDefault):
        user = self._cachedUsersBySerialNum.get(serialNum)
        if user is not None:
            return user
        return self.loadUser(serialNum, default)

    def userForExternalId(self, externalId, default=NoDefault):
        for user in self._cachedUsers:
            if user.externalId() == externalId:
                return user
        for user in self.users():
            if user.externalId() == externalId:
                return user
        if default is NoDefault:
            raise KeyError(externalId)
        return default

    def userForName(self, name, default=NoDefault):
        for user in self._cachedUsers:
            if user.name() == name:
                return user
        for user in self.users():
            if user.name() == name:
                return user
        if default is NoDefault:
            raise KeyError(name)
        return default

    def users(self):
        return _UserList(self)

    def activeUsers(self):
        return _UserList(self, lambda user: user.isActive())

    def inactiveUsers(self):
        return _UserList(self, lambda user: not user.isActive())

    # endregion UserManager concrete methods

    # region Encoder/decoder

    def encoder(self):
        return self._encoder

    def decoder(self):
        return self._decoder

    def setEncoderDecoder(self, encoder, decoder):
        self._encoder = encoder
        self._decoder = decoder

    # endregion Encoder/decoder


class UserMixIn:

    def filename(self):
        return os.path.join(
            self.manager().userDir(), f'{self.serialNum()}.user')

    def save(self):
        with open(self.filename(), 'wb') as f:
            self.manager().encoder()(self, f)


class _UserList:

    def __init__(self, mgr, filterFunc=None):
        self._mgr = mgr
        self._serialNums = mgr.scanSerialNums()
        self._count = len(self._serialNums)
        self._data = None
        if filterFunc:
            results = []
            for user in self:
                if filterFunc(user):
                    results.append(user)
            self._count = len(results)
            self._data = results

    def __getitem__(self, index):
        if index >= self._count:
            raise IndexError(index)
        if self._data:
            # We have the data directly. Just return it.
            return self._data[index]
        # We have a list of the serial numbers.
        # Get the user from the manager via the cache or loading.
        serialNum = self._serialNums[index]
        if serialNum in self._mgr._cachedUsersBySerialNum:
            return self._mgr._cachedUsersBySerialNum[serialNum]
        return self._mgr.loadUser(self._serialNums[index])

    def __len__(self):
        return self._count
