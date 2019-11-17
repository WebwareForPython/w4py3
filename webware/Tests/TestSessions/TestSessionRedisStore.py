# pylint: disable=unused-import,wrong-import-order
from . import redis  # noqa: F401 (mock redis installation)

from SessionRedisStore import SessionRedisStore

from .TestSessionMemoryStore import TestSessionMemoryStore


class SessionRedisStoreTest(TestSessionMemoryStore):

    _storeClass = SessionRedisStore

    def setUp(self):
        TestSessionMemoryStore.setUp(self)

    def tearDown(self):
        TestSessionMemoryStore.tearDown(self)

    def testCleanStaleSessions(self):
        self._store.cleanStaleSessions()
