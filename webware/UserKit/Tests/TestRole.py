"""Unittests for the Role classes."""

import unittest


class BasicRoleTest(unittest.TestCase):
    """Tests for the basic role class."""

    def roleClasses(self):
        """Return a list of all Role classes for testing."""
        from UserKit.Role import Role
        from UserKit.HierRole import HierRole
        return [Role, HierRole]

    def testRoleBasics(self):
        """Invoke testRole() with each class returned by roleClasses."""
        for roleClass in self.roleClasses():
            self.checkRoleClass(roleClass)

    def checkRoleClass(self, roleClass):
        role = roleClass('foo', 'bar')
        self.assertEqual(role.name(), 'foo')
        self.assertEqual(role.description(), 'bar')
        self.assertEqual(str(role), 'foo')

        role.setName('x')
        self.assertEqual(role.name(), 'x')

        role.setDescription('y')
        self.assertEqual(role.description(), 'y')

        self.assertTrue(role.playsRole(role))


class HierRoleTest(unittest.TestCase):
    """Tests for the hierarchical role class."""

    def testHierRole(self):
        from UserKit.HierRole import HierRole as hr
        animal = hr('animal')
        eggLayer = hr('eggLayer', None, [animal])
        furry = hr('furry', None, [animal])
        # pylint: disable=possibly-unused-variable
        snake = hr('snake', None, [eggLayer])
        dog = hr('dog', None, [furry])
        platypus = hr('platypus', None, [eggLayer, furry])
        vegetable = hr('vegetable')

        roles = locals()
        del roles['hr']
        del roles['self']

        # The tests below are one per line.
        # The first word is the role name. The rest of the words
        # are all the roles it plays (besides itself).
        tests = '''\
            eggLayer animal
            furry animal
            snake eggLayer animal
            dog furry animal
            platypus eggLayer furry animal'''

        tests = [test.split() for test in tests.splitlines()]

        # Strip names
        # Can we use a compounded/nested list comprehension for this?
        oldTest = tests
        tests = []
        for test in oldTest:
            test = [name.strip() for name in test]
            tests.append(test)

        # Now let's actually do some testing...
        for test in tests:
            role = roles[test[0]]
            self.assertTrue(role.playsRole(role))

            # Test that the role plays all the roles listed
            for name in test[1:]:
                playsRole = roles[name]
                self.assertTrue(role.playsRole(playsRole))

            # Now test that the role does NOT play
            # any of the other roles not listed
            otherRoles = roles.copy()
            for name in test:
                del otherRoles[name]
            for name in otherRoles:
                self.assertFalse(role.playsRole(roles[name]))
