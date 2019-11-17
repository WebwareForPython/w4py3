from SessionMemoryStore import SessionMemoryStore
from SessionFileStore import SessionFileStore

from .TestSessionMemoryStore import TestSessionMemoryStore


class SessionFileStoreTest(TestSessionMemoryStore):

    _storeClass = SessionFileStore
    _storeIsOrdered = False

    def testMemoryStoreRestoreFiles(self):
        app = self._app
        store = SessionMemoryStore(app)
        self.assertEqual(len(store), 7)
        self.assertTrue('foo-0' in store and 'foo-6' in store)
        store = SessionMemoryStore(app, restoreFiles=False)
        self.assertEqual(len(store), 0)
        self.assertFalse('foo-0' in store or 'foo-6' in store)

    def testFileStoreRestoreFiles(self):
        app = self._app
        store = SessionFileStore(app)
        self.assertEqual(len(store), 7)
        self.assertTrue('foo-0' in store and 'foo-6' in store)
        store = SessionFileStore(app, restoreFiles=False)
        self.assertEqual(len(store), 0)
        self.assertFalse('foo-0' in store or 'foo-6' in store)
