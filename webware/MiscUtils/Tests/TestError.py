import unittest

from MiscUtils.Error import Error


class DummyObject:

    def __repr__(self):
        return '<dummy>'


class TestError(unittest.TestCase):

    def testNone(self):
        err = Error(None, None)
        self.assertEqual(str(err), 'ERROR: None')
        self.assertEqual(repr(err),
                         'ERROR(object=None; message=None; data={})')
        self.assertIs(err.object(), None)
        self.assertIs(err.message(), None)

    def testObjMessage(self):
        obj = DummyObject()
        err = Error(obj, 'test')
        self.assertEqual(str(err), 'ERROR: test')
        self.assertEqual(
            repr(err),
            "ERROR(object=<dummy>; message='test'; data={})")
        self.assertIs(err.object(), obj)
        self.assertIs(err.message(), 'test')

    def testIsDict(self):
        err = Error(DummyObject(), 'test')
        self.assertIsInstance(err, dict)
        self.assertIsInstance(err, Error)

    def testValueDict(self):
        err = Error(DummyObject(), 'test', a=5, b='.')
        self.assertEqual(str(err), 'ERROR: test')
        self.assertEqual(
            repr(err),
            "ERROR(object=<dummy>; message='test'; data={'a': 5, 'b': '.'})")
        self.assertEqual(list(err), ['a', 'b'])
        self.assertIsInstance(err['a'], int)
        self.assertIsInstance(err['b'], str)

    def testVarArgs(self):
        err = Error(DummyObject(), 'test', {'a': 5}, b='.')
        self.assertEqual(str(err), 'ERROR: test')
        self.assertEqual(
            repr(err),
            "ERROR(object=<dummy>; message='test'; data={'a': 5, 'b': '.'})")
        self.assertEqual(list(err), ['a', 'b'])
        self.assertIsInstance(err['a'], int)
        self.assertIsInstance(err['b'], str)
