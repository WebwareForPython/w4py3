"""This module tests UserManagers in different permutations."""

import os
import shutil
import unittest


class UserManagerTest(unittest.TestCase):
    """Tests for the base UserManager class."""

    def setUp(self):
        from UserKit.UserManager import UserManager
        self._mgr = UserManager()

    def testSettings(self):
        mgr = self._mgr
        value = 5.1
        mgr.setModifiedUserTimeout(value)
        self.assertEqual(mgr.modifiedUserTimeout(), value)
        mgr.setCachedUserTimeout(value)
        self.assertEqual(mgr.cachedUserTimeout(), value)
        mgr.setActiveUserTimeout(value)
        self.assertEqual(mgr.activeUserTimeout(), value)

    def testUserClass(self):
        mgr = self._mgr
        from UserKit.User import User

        class SubUser(User):
            pass

        mgr.setUserClass(SubUser)
        self.assertEqual(
            mgr.userClass(), SubUser,
            "We should be able to set a custom user class.")

        class Poser:
            pass

        # Setting a customer user class that doesn't extend UserKit.User
        # should fail.
        with self.assertRaises(TypeError):
            mgr.setUserClass(Poser)

    def tearDown(self):
        self._mgr.shutDown()
        self._mgr = None


# pylint: disable=no-member

class UserManagerToSomewhereTest:
    """Common tests for all UserManager subclasses.

    This abstract class provides some tests that all user managers should pass.
    Subclasses are responsible for overriding setUp() and tearDown() for which
    they should invoke super.
    """

    def testBasics(self):
        mgr = self._mgr
        user = self._user = mgr.createUser('foo', 'bar')
        self.assertEqual(user.manager(), mgr)
        self.assertEqual(user.name(), 'foo')
        self.assertEqual(user.password(), 'bar')
        self.assertFalse(user.isActive())
        self.assertEqual(mgr.userForSerialNum(user.serialNum()), user)
        self.assertEqual(mgr.userForExternalId(user.externalId()), user)
        self.assertEqual(mgr.userForName(user.name()), user)
        externalId = user.externalId()  # for use later in testing

        users = mgr.users()
        self.assertEqual(len(users), 1)
        self.assertEqual(
            users[0], user, 'users[0]={users[0]!r}, user={user!r}')
        self.assertEqual(len(mgr.activeUsers()), 0)
        self.assertEqual(len(mgr.inactiveUsers()), 1)

        # login
        user2 = mgr.login(user, 'bar')
        self.assertEqual(user, user2)
        self.assertTrue(user.isActive())
        self.assertEqual(len(mgr.activeUsers()), 1)
        self.assertEqual(len(mgr.inactiveUsers()), 0)

        # logout
        user.logout()
        self.assertFalse(user.isActive())
        self.assertEqual(mgr.numActiveUsers(), 0)

        # login via user
        result = user.login('bar')
        self.assertEqual(result, user)
        self.assertTrue(user.isActive())
        self.assertEqual(mgr.numActiveUsers(), 1)

        # logout via user
        user.logout()
        self.assertFalse(user.isActive())
        self.assertEqual(mgr.numActiveUsers(), 0)

        # login a 2nd time, but with bad password
        user.login('bar')
        user.login('rab')
        self.assertFalse(user.isActive())
        self.assertEqual(mgr.numActiveUsers(), 0)

        # Check that we can access the user when he is not cached
        mgr.clearCache()
        user = mgr.userForSerialNum(1)
        self.assertTrue(user)
        self.assertEqual(user.password(), 'bar')

        mgr.clearCache()
        user = self._mgr.userForExternalId(externalId)
        self.assertTrue(user)
        self.assertEqual(user.password(), 'bar')

        mgr.clearCache()
        user = self._mgr.userForName('foo')
        self.assertTrue(user)
        self.assertEqual(user.password(), 'bar')

    def testUserAccess(self):
        mgr = self._mgr
        user = mgr.createUser('foo', 'bar')

        self.assertEqual(mgr.userForSerialNum(user.serialNum()), user)
        self.assertEqual(mgr.userForExternalId(user.externalId()), user)
        self.assertEqual(mgr.userForName(user.name()), user)

        self.assertRaises(KeyError, mgr.userForSerialNum, 1000)
        self.assertRaises(KeyError, mgr.userForExternalId, 'asdf')
        self.assertRaises(KeyError, mgr.userForName, 'asdf')

        self.assertEqual(mgr.userForSerialNum(1000, 1), 1)
        self.assertEqual(mgr.userForExternalId('asdf', 1), 1)
        self.assertEqual(mgr.userForName('asdf', 1), 1)

    def testDuplicateUser(self):
        mgr = self._mgr
        user = self._user = mgr.createUser('foo', 'bar')
        self.assertEqual(user.name(), 'foo')
        self.assertRaises(KeyError, mgr.createUser, 'foo', 'bar')
        userClass = mgr.userClass()
        self.assertRaises(KeyError, userClass, mgr, 'foo', 'bar')


class UserManagerToFileTest(UserManagerToSomewhereTest, unittest.TestCase):
    """Tests for the UserManagerToFile class."""

    def setUp(self):
        from UserKit.UserManagerToFile import UserManagerToFile
        self._mgr = UserManagerToFile()
        self.setUpUserDir(self._mgr)

    def setUpUserDir(self, mgr):
        path = 'Users'
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        os.mkdir(path)
        mgr.setUserDir(path)

    def tearDown(self):
        path = 'Users'
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)


class RoleUserManagerToFileTest(UserManagerToFileTest, unittest.TestCase):
    """Tests for the RoleUserManagerToFile class."""

    def setUp(self):
        from UserKit.RoleUserManagerToFile import RoleUserManagerToFile
        self._mgr = RoleUserManagerToFile()
        self.setUpUserDir(self._mgr)
