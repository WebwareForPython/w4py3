from SessionShelveStore import SessionShelveStore

from .TestSessionMemoryStore import TestSessionMemoryStore


class SessionShelveStoreTest(TestSessionMemoryStore):

    _storeClass = SessionShelveStore
    _storeIsOrdered = False

    def testFileShelveRestoreFiles(self):
        app = self._app
        store = self._store
        self.assertEqual(len(store), 7)
        session = store['foo-3']
        self.assertTrue('foo-0' in store and 'foo-6' in store)
        store = SessionShelveStore(
            app, restoreFiles=False, filename='Session.Store2')
        self.assertEqual(len(store), 0)
        self.assertFalse('foo-0' in store or 'foo-6' in store)
        store['foo-3'] = session
        store.storeAllSessions()
        store = SessionShelveStore(app, filename='Session.Store2')
        self.assertEqual(len(store), 1)
        self.assertTrue('foo-3' in store)
        self.assertFalse('foo-0' in store or 'foo-6' in store)
