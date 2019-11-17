"""Mock Webware Application class."""


class Application:
    """Mock application."""

    _sessionDir = 'SessionStoreTestDir'
    _alwaysSaveSessions = True
    _retainSessions = True
    _sessionTimeout = 60 * 60
    _sessionPrefix = ''
    _sessionName = '_SID_'

    def setting(self, key, default=None):
        return dict(
            SessionTimeout=self._sessionTimeout // 60,
            SessionPrefix=self._sessionPrefix,
            SessionName=self._sessionName,
            DynamicSessionTimeout=1,
            MaxDynamicMemorySessions=3,
            MemcachedOnIteration=None,
            Debug=dict(Sessions=False),
        ).get(key, default)

    def handleException(self):
        raise Exception('Application Error')

    def sessionTimeout(self, _trans=None):
        return self._sessionTimeout

    def sessionPrefix(self, _trans=None):
        return self._sessionPrefix

    def sessionName(self, _trans=None):
        return self._sessionName

    def hasSession(self, _sessionId):
        return False
