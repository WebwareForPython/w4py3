"""Webware for Python"""


def addToSearchPath():
    """Add the Webware package to the search path for Python modules."""
    import sys
    webwarePath = __path__[0]
    if webwarePath not in sys.path:
        sys.path.insert(0, webwarePath)


def mockAppWithPlugins(path=None, settings=None, development=None):
    """Return a mock application with all plugins loaded."""
    addToSearchPath()
    from MockApplication import MockApplication
    from PlugInLoader import PlugInLoader
    app = MockApplication(path, settings, development)
    PlugInLoader(app).loadPlugIns()
    return app
