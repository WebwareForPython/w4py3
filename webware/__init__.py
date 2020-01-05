"""Webware for Python"""

import sys


def add_to_python_path():
    webwarePath = __path__[0]
    if webwarePath not in sys.path:
        sys.path.insert(0, webwarePath)


def load_plugins(path, settings=None, development=None):
    from MockApplication import MockApplication
    from PlugInLoader import PlugInLoader
    app = MockApplication(path, settings, development)
    loader = PlugInLoader(app)
    loader.loadPlugIns(app.setting('PlugIns'), verbose=False)
