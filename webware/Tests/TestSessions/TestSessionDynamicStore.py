from SessionDynamicStore import SessionDynamicStore

from .TestSessionMemoryStore import TestSessionMemoryStore


class SessionDynamicStoreTest(TestSessionMemoryStore):

    _storeClass = SessionDynamicStore

    def testCleanStaleSessions(self):
        store = self._store
        memoryStore = store._memoryStore  # pylint: disable=no-member
        fileStore = store._fileStore  # pylint: disable=no-member
        self.assertEqual(len(memoryStore), 7)
        self.assertEqual(len(fileStore), 0)
        TestSessionMemoryStore.testCleanStaleSessions(self)
        self.assertEqual(len(memoryStore), 3)
        self.assertEqual(len(fileStore), 2)
        self.assertTrue('foo-0' in memoryStore and 'foo-2' in memoryStore)
        self.assertTrue('foo-3' in fileStore and 'foo-4' in fileStore)
