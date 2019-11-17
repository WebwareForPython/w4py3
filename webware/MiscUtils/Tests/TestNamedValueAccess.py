import unittest

from MiscUtils import AbstractError, NoDefault
from MiscUtils.NamedValueAccess import (
    NamedValueAccessError, valueForKey, valueForName)


class T:  # pylint: disable=invalid-name
    pass


class T1(T):

    def foo(self):
        return 1


class T2(T):

    def _foo(self):
        return 1


class T3(T):

    def foo(self):
        return 1

    def _foo(self):
        return 0


class T4(T):

    def foo(self):
        return 1

    def __init__(self):
        self._foo = 0


class T5(T):

    def __init__(self):
        self.foo = 0

    def _foo(self):
        return 1


class T6(T):

    def __init__(self):
        self.foo = 1
        self._foo = 0


# Make a list of all the 'T' classes which are used in testing
tClasses = [globals()[name] for name in dir()
            if name.startswith('T') and name[1:].isdigit()]


class LookupTest:
    """Abstract super class for the test cases covering the functions.

    Subclasses must implement self.lookup() and can make use of
    self.classes and self.objs.
    """

    def setUp(self):
        self.setUpClasses()
        self.setUpObjects()

    def setUpClasses(self):
        self.classes = tClasses

    def setUpObjects(self):
        self.objs = [klass() for klass in self.classes]

    def lookup(self, obj, key, default=NoDefault):
        raise AbstractError(self.__class__)

    def testBasicAccess(self):
        """Check the basic access functionality.

        Invoke the look up function with key 'foo', expecting 1 in return.
        Invoke the look up with 'bar', expected an exception.
        Invoke the look up with 'bar' and default 2, expecting 2.
        """
        func = self.lookup
        # pylint: disable=assignment-from-no-return,no-member
        for obj in self.objs:
            value = func(obj, 'foo')
            self.assertEqual(value, 1, 'value = %r, obj = %r' % (value, obj))
            self.assertRaises(NamedValueAccessError, func, obj, 'bar')
            value = func(obj, 'bar', 2)
            self.assertEqual(value, 2, 'value = %r, obj = %r' % (value, obj))

    def testBasicAccessRepeated(self):
        """Just repeat checkBasicAccess multiple times to check stability."""
        for _count in range(50):
            # Yes, it's safe to invoke this other particular test
            # multiple times without the usual setUp()/tearDown() cycle
            self.testBasicAccess()


class ValueForKeyTest(LookupTest, unittest.TestCase):

    def lookup(self, obj, key, default=NoDefault):
        return valueForKey(obj, key, default)


class ValueForNameTest(LookupTest, unittest.TestCase):

    def lookup(self, obj, key, default=NoDefault):
        return valueForName(obj, key, default)

    def testNamedValueAccess(self):
        objs = self.objs

        # link the objects
        for i in range(len(objs)-1):
            objs[i].nextObject = objs[i+1]

        # test the links
        for i in range(len(objs)):
            name = 'nextObject.' * i + 'foo'
            self.assertEqual(self.lookup(objs[0], name), 1)

    def testDicts(self):
        d = {'origin': {'x': 1, 'y': 2},
             'size': {'width': 3, 'height': 4}}
        obj = self.objs[0]
        obj.rect = d

        self.assertEqual(self.lookup(d, 'origin.x'), 1)
        self.assertTrue(self.lookup(obj, 'rect.origin.x'))

        self.assertRaises(NamedValueAccessError, self.lookup, d, 'bar')
        self.assertRaises(NamedValueAccessError, self.lookup, obj, 'bar')

        self.assertEqual(self.lookup(d, 'bar', 2), 2)
        self.assertEqual(self.lookup(obj, 'rect.bar', 2), 2)
