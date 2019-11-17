"""Tests various functions of Users and Roles by running example code."""

import shutil
import tempfile
import unittest


class SimpleExampleTest(unittest.TestCase):
    """A simple example to illustrate how to use UserKit."""

    def setUp(self):
        """Make a folder for UserManager data."""
        self._userDataDir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove our test folder for UserManager data."""
        shutil.rmtree(self._userDataDir, ignore_errors=True)

    def testUsersNoRoles(self):
        from UserKit.UserManagerToFile import UserManagerToFile

        userManager = UserManagerToFile()
        userManager.setUserDir(self._userDataDir)

        # Create a user, add to 'staff' role
        fooUser = userManager.createUser('foo', 'bar')

        # bad login
        theUser = userManager.loginName('foo', 'badpass')
        self.assertTrue(
            theUser is None, 'loginName() returns null if login failed.')
        self.assertFalse(
            fooUser.isActive(),
            'User should NOT be logged in since password was incorrect.')

        # good login
        theUser = userManager.loginName('foo', 'bar')
        self.assertTrue(theUser.isActive(), 'User should be logged in now')
        self.assertEqual(
            theUser, fooUser,
            'Should be the same user object, since it is the same user "foo"')

        # logout
        theUser.logout()
        self.assertFalse(
            theUser.isActive(), 'User should no longer be active.')
        self.assertEqual(userManager.numActiveUsers(), 0)

    def testUsersAndRoles(self):
        from UserKit.RoleUserManagerToFile import RoleUserManagerToFile
        from UserKit.HierRole import HierRole
        from hashlib import sha1 as sha

        userManager = RoleUserManagerToFile()
        userManager.setUserDir(self._userDataDir)

        # Setup our roles
        customersRole = HierRole('customers', 'Customers of ACME Industries')
        staffRole = HierRole(
            'staff', 'All staff.'
            ' Staff role includes all permissions of Customers role.',
            [customersRole])

        # Create a user, add to 'staff' role
        # Note that I encrypt my passwords here so they don't appear
        # in plaintext in the storage file.
        johnUser = userManager.createUser('john', sha(b'doe').hexdigest())
        johnUser.setRoles([customersRole])

        fooUser = userManager.createUser('foo', sha(b'bar').hexdigest())
        fooUser.setRoles([staffRole])

        # Check user "foo"
        theUser = userManager.loginName('foo', sha(b'bar').hexdigest())
        self.assertTrue(theUser.isActive(), 'User should be logged in now')
        self.assertEqual(
            theUser, fooUser,
            'Should be the same user object, since it is the same user "foo"')
        self.assertTrue(
            theUser.playsRole(staffRole),
            'User "foo" should be a member of the staff role.')
        self.assertTrue(
            theUser.playsRole(customersRole), 'User "foo" should'
            ' also be in customer role, since staff includes customers.')

        # Check user "John"
        theUser = userManager.loginName('john', sha(b'doe').hexdigest())
        self.assertTrue(theUser.isActive(), 'User should be logged in now.')
        self.assertEqual(
            theUser, johnUser, 'Should be the same user object,'
            ' since it is the same user "John".')
        self.assertFalse(
            theUser.playsRole(staffRole),
            'John should not be a member of the staff.')
        self.assertTrue(
            theUser.playsRole(customersRole),
            'John should play customer role.')
