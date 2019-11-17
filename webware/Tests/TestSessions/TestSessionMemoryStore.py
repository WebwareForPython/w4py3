import os

from SessionMemoryStore import SessionMemoryStore

from .Session import Session
from .TestSessionStore import TestSessionStore


class TestSessionMemoryStore(TestSessionStore):

    _storeClass = SessionMemoryStore
    _storeIsOrdered = True

    def setUp(self):
        d = self._app._sessionDir
        if not os.path.exists(d):
            os.mkdir(d)
        TestSessionStore.setUp(self)
        self._store.clear()
        for n in range(7):
            session = Session(n)
            self._store[session.identifier()] = session
            self.assertFalse(session.isExpired())

    def tearDown(self):
        self._store.clear()
        self._store.storeAllSessions()
        d = self._app._sessionDir
        for filename in os.listdir(d):
            os.remove(os.path.join(d, filename))
        os.rmdir(d)
        TestSessionStore.tearDown(self)

    def testLen(self):
        self.assertEqual(len(self._store), 7)

    def testGetItem(self):
        store = self._store
        self.assertEqual(self._store['foo-3'].bar(), 18)
        self.assertRaises(KeyError, store.__getitem__, 'foo-7')

    def testSetItem(self):
        session = Session()
        key = session.identifier()
        self._store[key] = session
        self.assertEqual(self._store[key].data(), session.data())

    def testDelItem(self):
        del self._store['foo-3']
        self.assertFalse('foo-3' in self._store)
        self.assertEqual(Session._lastExpired, 'foo-3')
        try:
            self._store['foo-3']
        except KeyError:
            pass
        self.assertRaises(KeyError, self._store.__delitem__, 'foo-3')

    def testContains(self):
        store = self._store
        self.assertTrue(
            'foo-0' in store and 'foo-3' in store and 'foo-6' in store)
        self.assertFalse('foo' in store)
        self.assertFalse('0' in store or '3' in store or '6' in store)
        self.assertFalse('foo-7' in store)

    def testIter(self):
        keys = list(iter(self._store))
        expectedKeys = [f'foo-{n}' for n in range(7)]
        if not self._storeIsOrdered:
            keys = set(keys)
            expectedKeys = set(expectedKeys)
        self.assertEqual(keys, expectedKeys)

    def testKeys(self):
        keys = self._store.keys()  # pylint: disable=assignment-from-no-return
        self.assertTrue(isinstance(keys, list))
        expectedKeys = [f'foo-{n}' for n in range(7)]
        if not self._storeIsOrdered:
            keys = set(keys)
            expectedKeys = set(expectedKeys)
        self.assertEqual(keys, expectedKeys)

    def testClear(self):
        store = self._store
        store.clear()
        self.assertFalse(
            'foo-0' in store or 'foo-3' in store or 'foo-6' in store)

    def testSetDefault(self):
        store = self._store
        session = Session()
        self.assertEqual(store.setdefault('foo-3').bar(), 18)
        self.assertEqual(store.setdefault('foo-3', session).bar(), 18)
        self.assertEqual(store.setdefault('foo-7', session).bar(), 42)
        self.assertEqual(store.setdefault('foo-7').bar(), 42)

    def testPop(self):
        store = self._store
        session = self._store['foo-3']
        self.assertFalse(session.isExpired())
        self.assertEqual(store.pop('foo-3').bar(), 18)
        self.assertRaises(KeyError, store.pop, 'foo-3')
        self.assertEqual(store.pop('foo-3', Session()).bar(), 42)
        self.assertRaises(KeyError, store.pop, 'foo-3')
        self.assertFalse(session.isExpired())

    def testGet(self):
        self.assertEqual(self._store.get('foo-4').bar(), 24)
        self.assertEqual(self._store.get('foo-4', Session()).bar(), 24)
        self.assertEqual(self._store.get('foo-7'), None)
        self.assertEqual(self._store.get('foo-7', Session()).bar(), 42)

    def testStoreSession(self):
        session = self._store['foo-3']
        self.assertEqual(session.bar(), 18)
        session.setBar(19)
        self.assertEqual(session.bar(), 19)
        self._store.storeSession(session)
        session = self._store['foo-3']
        self.assertEqual(session.bar(), 19)
        session = Session(3, 20)
        self._store.storeSession(session)
        session = self._store['foo-3']
        self.assertEqual(session.bar(), 20)
        session = Session()
        self._store.storeSession(session)
        session = self._store['foo-7']
        self.assertEqual(session.bar(), 42)

    def testItems(self):
        items = self._store.items()
        self.assertTrue(isinstance(items, list))
        self.assertEqual(len(items), 7)
        self.assertTrue(isinstance(items[4], tuple))
        self.assertEqual(len(items[4]), 2)
        self.assertEqual(dict(items)['foo-3'].bar(), 18)

    def testIterItems(self):
        items = iter(self._store.items())
        self.assertFalse(isinstance(items, list))
        items = list(items)
        self.assertTrue(isinstance(items[4], tuple))
        self.assertEqual(len(items[4]), 2)
        self.assertEqual(dict(items)['foo-3'].bar(), 18)

    def testValues(self):
        values = self._store.values()
        self.assertTrue(isinstance(values, list))
        self.assertEqual(len(values), 7)
        value = values[4]
        self.assertTrue(isinstance(value, Session))
        self.assertEqual(self._store[value.identifier()].bar(), value.bar())

    def testIterValues(self):
        values = iter(self._store.values())
        self.assertFalse(isinstance(values, list))
        values = list(values)
        self.assertEqual(len(values), 7)
        value = values[4]
        self.assertTrue(isinstance(value, Session))
        self.assertEqual(self._store[value.identifier()].bar(), value.bar())

    def testCleanStaleSessions(self):
        store = self._store
        self.assertEqual(len(store), 7)
        self.assertTrue('foo-0' in store and 'foo-4' in store)
        self.assertTrue('foo-5' in store and 'foo-6' in store)
        store.cleanStaleSessions()
        self.assertEqual(len(store), 5)
        self.assertTrue('foo-0' in store and 'foo-4' in store)
        self.assertFalse('foo-5' in store or 'foo-6' in store)
