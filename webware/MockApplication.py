import os

from ConfigurableForServerSidePath import ConfigurableForServerSidePath


class MockImportManager(object):

    def recordFile(self, filename, isfile=None):
        pass


defaultConfig = dict(
    CacheDir='Cache',
    PlugIns=['MiscUtils', 'WebUtils', 'TaskKit', 'UserKit', 'PSP'],
)


class MockApplication(ConfigurableForServerSidePath):

    def __init__(self, path=None, settings=None, development=None):
        ConfigurableForServerSidePath.__init__(self)
        if path is None:
            path = os.getcwd()
        self._serverSidePath = os.path.abspath(path)
        self._webwarePath = os.path.abspath(os.path.dirname(__file__))
        if development is None:
            development = bool(os.environ.get('WEBWARE_DEVELOPMENT'))
        self._development = development

        appConfig = self.config()  # get and cache the configuration
        if settings:
            appConfig.update(settings)
        self._cacheDir = self.serverSidePath(self.setting('CacheDir') or 'Cache')
        from MiscUtils.PropertiesObject import PropertiesObject
        props = PropertiesObject(os.path.join(
            self._webwarePath, 'Properties.py'))
        self._webwareVersion = props['version']
        self._webwareVersionString = props['versionString']
        self._imp = MockImportManager()
        for path in (self._cacheDir,):
            if path and not os.path.exists(path):
                os.makedirs(path)

    def defaultConfig(self):
        return defaultConfig

    def configReplacementValues(self):
        """Get config values that need to be escaped."""
        return dict(
            ServerSidePath=self._serverSidePath,
            WebwarePath=self._webwarePath,
            Development=self._development)

    def configFilename(self):
        return self.serverSidePath('Configs/Application.config')

    def serverSidePath(self, path=None):
        if path:
            return os.path.normpath(
                os.path.join(self._serverSidePath, path))
        return self._serverSidePath

    def hasContext(self, context):
        return False

    def addServletFactory(self, factory):
        pass
