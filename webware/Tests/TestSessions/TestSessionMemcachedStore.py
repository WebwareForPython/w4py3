# pylint: disable=unused-import,wrong-import-order
from . import memcache  # noqa: F401 (mock memcache installation)

from SessionMemcachedStore import SessionMemcachedStore

from .TestSessionMemoryStore import TestSessionMemoryStore


class SessionMemcachedStoreTest(TestSessionMemoryStore):

    _storeClass = SessionMemcachedStore

    def setUp(self):
        TestSessionMemoryStore.setUp(self)
        self.setOnIteration()

    def tearDown(self):
        self.setOnIteration()
        TestSessionMemoryStore.tearDown(self)

    def setOnIteration(self, onIteration=None):
        self._store._onIteration = onIteration

    def testLen(self):
        self.assertEqual(len(self._store), 0)
        self.setOnIteration('Error')
        with self.assertRaises(NotImplementedError):
            len(self._store)

    def testIter(self):
        keys = [key for key in self._store]
        self.assertEqual(keys, [])
        self.setOnIteration('Error')
        with self.assertRaises(NotImplementedError):
            [key for key in self._store]  # pylint: disable=pointless-statement

    def testKeys(self):
        keys = self._store.keys()  # pylint: disable=assignment-from-no-return
        self.assertEqual(keys, [])
        self.setOnIteration('Error')
        with self.assertRaises(NotImplementedError):
            self._store.keys()

    def testItems(self):
        items = self._store.items()
        self.assertEqual(items, [])
        self.setOnIteration('Error')
        with self.assertRaises(NotImplementedError):
            self._store.items()

    def testIterItems(self):
        items = [key for key in self._store.iteritems()]
        self.assertEqual(items, [])
        self.setOnIteration('Error')
        with self.assertRaises(NotImplementedError):
            # pylint: disable=expression-not-assigned
            [key for key in self._store.iteritems()]

    def testValues(self):
        values = self._store.values()
        self.assertEqual(values, [])
        self.setOnIteration('Error')
        with self.assertRaises(NotImplementedError):
            self._store.values()

    def testIterValues(self):
        values = [key for key in self._store.values()]
        self.assertEqual(values, [])
        self.setOnIteration('Error')
        with self.assertRaises(NotImplementedError):
            self._store.values()

    def testClear(self):
        self._store.clear()
        self.setOnIteration('Error')
        with self.assertRaises(NotImplementedError):
            self._store.clear()

    def testCleanStaleSessions(self):
        self._store.cleanStaleSessions()
