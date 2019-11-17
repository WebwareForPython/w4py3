import unittest

from Session import Session, SessionError

from .Transaction import Transaction


class TestSession(unittest.TestCase):

    def testInit(self):
        transaction = Transaction()
        session = Session(transaction)
        identifier = session.identifier()
        self.assertIsInstance(identifier, str)
        self.assertEqual(len(identifier), 47)
        session = Session(transaction, 'test-identifier')
        self.assertEqual(session.identifier(), 'test-identifier')
        with self.assertRaises(SessionError):
            Session(transaction, 'invalid+identifier')

    def testUniqueIds(self):
        transaction = Transaction()
        identifiers = set()
        for _count in range(3):
            session = Session(transaction)
            identifier = session.identifier()
            self.assertIsInstance(identifier, str)
            self.assertEqual(len(identifier), 47)
            parts = identifier.split('-')
            self.assertEqual(len(parts), 2)
            self.assertEqual(len(parts[0]), 14)
            self.assertEqual(len(parts[1]), 32)
            self.assertTrue(parts[0].isdigit())
            self.assertTrue(all(c in '0123456789abcdef' for c in parts[1]))
            self.assertNotIn(identifier, identifiers)
            identifiers.add(identifier)

    def testCreationAndAccessTime(self):
        transaction = Transaction()
        session = Session(transaction, 'test')
        t = session.creationTime()
        self.assertIsInstance(t, float)
        self.assertEqual(session.creationTime(), session.lastAccessTime())
        session = Session(transaction, 'test2')
        self.assertGreaterEqual(session.creationTime(), t)

    def testIsDirty(self):
        transaction = Transaction()
        session = Session(transaction, 'test')
        self.assertIs(session.isDirty(), False)
        session.setValue('test', None)
        self.assertIs(session.isDirty(), True)

    def testIsExpired(self):
        transaction = Transaction()
        session = Session(transaction, 'test')
        self.assertIs(session.isExpired(), False)
        session.expiring()
        self.assertIs(session.isExpired(), True)

    def testIsNew(self):
        transaction = Transaction()
        session = Session(transaction, 'test')
        self.assertIs(session.isNew(), True)
        session.awake(transaction)
        self.assertIs(session.isNew(), True)
        session.awake(transaction)
        self.assertIs(session.isNew(), False)

    def testTimeout(self):
        transaction = Transaction()
        session = Session(transaction, 'test')
        self.assertEqual(session.timeout(), 3600)
        session.setTimeout(3700)
        self.assertEqual(session.timeout(), 3700)
        session.invalidate()
        self.assertEqual(session.timeout(), 0)

    def testValues(self):
        transaction = Transaction()
        session = Session(transaction, 'test')
        self.assertRaises(KeyError, session.value, 'a')
        self.assertIsNone(session.value('a', None))
        self.assertEqual(session.value('a', 0), 0)
        self.assertEqual(session.value('a', 'foo'), 'foo')
        self.assertIs(session.hasValue('a'), False)
        session.setValue('a', None)
        self.assertIsNone(session.value('a'))
        self.assertIsNone(session.value('a', 'foo'))
        self.assertIs(session.hasValue('a'), True)
        session.delValue('a')
        self.assertRaises(KeyError, session.value, 'a')
        self.assertRaises(KeyError, session.delValue, 'a')
        self.assertIs(session.hasValue('a'), False)
        session.setValue('a', 'foo')
        self.assertEqual(session.value('a'), 'foo')
        self.assertEqual(session.value('a', None), 'foo')
        self.assertIs(session.hasValue('a'), True)
        session.setValue('b', 'bar')
        self.assertEqual(session.value('a'), 'foo')
        self.assertEqual(session.value('b'), 'bar')
        self.assertIs(session.hasValue('b'), True)
        self.assertIsInstance(session.values(), dict)
        self.assertEqual(session.values(), {'a': 'foo', 'b': 'bar'})

    def testDirectAccess(self):
        transaction = Transaction()
        session = Session(transaction, 'test')
        with self.assertRaises(KeyError):
            session['a']  # pylint: disable=pointless-statement
        self.assertNotIn('a', session)
        session['a'] = 'foo'
        self.assertEqual(session['a'], 'foo')
        self.assertIn('a', session)
        self.assertEqual(session.value('a'), 'foo')
        self.assertTrue(session.hasValue('a'))
        del session['a']
        with self.assertRaises(KeyError):
            session['a']  # pylint: disable=pointless-statement
        self.assertNotIn('a', session)
        self.assertFalse(session.hasValue('a'))

    def testSessionEncode(self):
        transaction = Transaction()
        session = Session(transaction, 'test')
        self.assertEqual(session.sessionEncode('myurl'), 'myurl?_SID_=test')
        self.assertEqual(
            session.sessionEncode('http://localhost/Webware/Servlet?a=1&b=2'),
            'http://localhost/Webware/Servlet?a=1&b=2&_SID_=test')
