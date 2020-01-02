import os
import sys

from MiscUtils.PropertiesObject import PropertiesObject


class PlugInError(Exception):
    """Plug-in error."""


class PlugIn:
    """Template for Webware Plug-ins.

    A plug-in is a software component that is loaded by Webware in order to
    provide additional Webware functionality without necessarily having to
    modify Webware's source. The most infamous plug-in is PSP (Python Server
    Pages) which ships with Webware.

    Plug-ins often provide additional servlet factories, servlet subclasses,
    examples and documentation. Ultimately, it is the plug-in author's choice
    as to what to provide and in what manner.

    Instances of this class represent plug-ins which are ultimately Python
    packages.

    A plug-in must also be a Webware component which means that it will have
    a Properties.py file advertising its name, version, requirements, etc.
    You can ask a plug-in for its properties().

    The plug-in/package must have an __init__.py which must contain the
    following function::

        def installInWebware(application):
            ...

    This function is invoked to take whatever actions are needed to plug the
    new component into Webware. See PSP for an example.

    If you ask an Application for its plugIns(), you will get a list of
    instances of this class.

    The path of the plug-in is added to sys.path, if it's not already there.
    This is convenient, but we may need a more sophisticated solution in the
    future to avoid name collisions between plug-ins.

    Note that this class is hardly ever subclassed. The software in the
    plug-in package is what provides new functionality and there is currently
    no way to tell the Application to use custom subclasses of this class on a
    case-by-case basis (and so far there is currently no need).

    Instructions for invoking::

        # 'self' is typically Application. It gets passed to installInWebware()
        p = PlugIn(self, 'Foo', '../Foo')
        willNotLoadReason = plugIn.load()
        if willNotLoadReason:
            print(f'Plug-in {path} cannot be loaded because:')
            print(willNotLoadReason)
            return None
        p.install()
        # Note that load() and install() could raise exceptions.
        # You should expect this.
    """

    # region Init, load and install

    def __init__(self, application, name, module):
        """Initializes the plug-in with basic information.

        This lightweight constructor does not access the file system.
        """
        self._app = application
        self._name = name
        self._module = module
        self._path = module.__path__[0]
        try:
            self._builtin = module.__package__ == f'webware.{name}'
        except AttributeError:
            self._builtin = False
        self._dir = os.path.dirname(self._path)
        self._cacheDir = os.path.join(self._app._cacheDir, self._name)
        self._examplePages = self._examplePagesContext = None

    def load(self, verbose=True):
        """Loads the plug-in into memory, but does not yet install it.

        Will return None on success, otherwise a message (string) that says
        why the plug-in could not be loaded.
        """
        if verbose:
            print(f'Loading plug-in: {self._name} at {self._path}')

        # Grab the Properties.py
        self._properties = PropertiesObject(
            self.serverSidePath('Properties.py'))

        if self._builtin and 'version' not in self._properties:
            self._properties['version'] = self._app._webwareVersion
            self._properties['versionString'] = self._app._webwareVersionString

        if not self._properties['willRun']:
            return self._properties['willNotRunReason']

        # Update sys.path
        if self._dir not in sys.path:
            sys.path.append(self._dir)

        # Inspect it and verify some required conventions
        if not hasattr(self._module, 'installInWebware'):
            raise PlugInError(
                f"Plug-in '{self._name!r}' in {self._dir!r}"
                " has no installInWebware() function.")

        # Give the module a pointer back to us
        setattr(self._module, 'plugIn', self)

        # Make a subdirectory for it in the Cache directory:
        if not os.path.exists(self._cacheDir):
            os.mkdir(self._cacheDir)

        self.setUpExamplePages()

    def setUpExamplePages(self):
        """Add a context for the examples."""
        if self._app.hasContext('Examples'):
            config = self._properties.get('webwareConfig', {})
            self._examplePages = config.get('examplePages') or None
            if self.hasExamplePages():
                examplesPath = self.serverSidePath('Examples')
                if not os.path.exists(examplesPath):
                    raise PlugInError(
                        f'Plug-in {self._name!r} says it has example pages, '
                        'but there is no Examples/ subdir.')
                if os.path.exists(os.path.join(examplesPath, '__init__.py')):
                    ctxName = self._name + '/Examples'
                    if not self._app.hasContext(ctxName):
                        self._app.addContext(ctxName, examplesPath)
                    self._examplePagesContext = ctxName
                else:
                    raise PlugInError(
                        'Cannot create Examples context for'
                        f' plug-in {self._name!r} (no __init__.py found).')

    def examplePages(self):
        return self._examplePages

    def hasExamplePages(self):
        return self._examplePages is not None

    def examplePagesContext(self):
        return self._examplePagesContext

    def install(self):
        """Install plug-in by invoking its installInWebware() function."""
        self._module.installInWebware(self._app)

    # endregion Init, load and install

    # region Access

    def name(self):
        """Return the name of the plug-in. Example: 'Foo'"""
        return self._name

    def directory(self):
        """Return the directory in which the plug-in resides. Example: '..'"""
        return self._dir

    def path(self):
        """Return the full path of the plug-in. Example: '../Foo'"""
        return self._path

    def serverSidePath(self, path=None):
        if path:
            return os.path.normpath(os.path.join(self._path, path))
        return self._path

    def module(self):
        """Return the Python module object of the plug-in."""
        return self._module

    def properties(self):
        """Return the properties.

        This is a dictionary-like object, of the plug-in which comes
        from its Properties.py file. See MiscUtils.PropertiesObject.py.
        """
        return self._properties

    # endregion Access
