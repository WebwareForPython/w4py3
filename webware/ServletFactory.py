"""Servlet factory template."""

import os
import sys
import threading

from keyword import iskeyword

from MiscUtils import AbstractError

from Servlet import Servlet

debug = False


class ServletFactory:
    """Servlet factory template.

    ServletFactory is an abstract class that defines the protocol for
    all servlet factories.

    Servlet factories are used by the Application to create servlets
    for transactions.

    A factory must inherit from this class and override uniqueness(),
    extensions() and either loadClass() or servletForTransaction().
    Do not invoke the base class methods as they all raise AbstractErrors.

    Each method is documented below.
    """

    # region Init

    def __init__(self, application):
        """Create servlet factory.

        Stores a reference to the application in self._app, because
        subclasses may or may not need to talk back to the application
        to do their work.
        """
        self._app = application
        self._imp = self._app._imp
        self._cacheClasses = self._app.setting("CacheServletClasses", True)
        self._cacheInstances = self._app.setting("CacheServletInstances", True)
        self._reloadClasses = self._app.setting("ReloadServletClasses", True)
        # All caches are keyed on the path.
        # _classCache caches the servlet classes,
        # in dictionaries with keys 'mtime' and 'class'.
        # 'mtime' is the modification time of the enclosing module.
        self._classCache = {}
        # _servletPool has lists of free reusable servlets
        self._servletPool = {}
        # _threadsafeServletCache has threadsafe servlets
        # (which are not pooled, so only one is kept at a time)
        self._threadsafeServletCache = {}
        self._importLock = threading.RLock()

    # endregion Init

    # region Info

    def name(self):
        """Return the name of the factory.

        This is a convenience for the class name.
        """
        return self.__class__.__name__

    def uniqueness(self):
        """Return uniqueness type.

        Returns a string to indicate the uniqueness of the ServletFactory's
        servlets. The Application needs to know if the servlets are unique
        per file, per extension or per application.

        Return values are 'file', 'extension' and 'application'.

        NOTE: Application so far only supports 'file' uniqueness.
        """
        raise AbstractError(self.__class__)

    def extensions(self):
        """Return a list of extensions that match this handler.

        Extensions should include the dot. An empty string indicates a file
        with no extension and is a valid value. The extension '.*' is a special
        case that is looked for a URL's extension doesn't match anything.
        """
        raise AbstractError(self.__class__)

    # endregion Info

    # region Import

    def importAsPackage(self, transaction, serverSidePathToImport):
        """Import requested module.

        Imports the module at the given path in the proper package/subpackage
        for the current request. For example, if the transaction has the URL
        http://localhost/Webware/MyContextDirectory/MySubdirectory/MyPage
        and path = 'some/random/path/MyModule.py' and the context is configured
        to have the name 'MyContext' then this function imports the module at
        that path as MyContext.MySubdirectory.MyModule . Note that the context
        name may differ from the name of the directory containing the context,
        even though they are usually the same by convention.

        Note that the module imported may have a different name from the
        servlet name specified in the URL. This is used in PSP.
        """

        # Pull out the full server side path and the context path
        request = transaction.request()
        path = request.serverSidePath()
        contextPath = request.serverSideContextPath()
        fullname = request.contextName()

        # There is no context, so import the module standalone
        # and give it a unique name:
        if not fullname or not path.startswith(contextPath):
            fullname = serverSidePathToImport
            if os.sep != '/':
                fullname = fullname.replace(os.sep, '_')
            fullname = fullname.replace('/', '_').replace('.', '_')
            name = os.path.splitext(os.path.basename(
                serverSidePathToImport))[0]
            moduleDir = os.path.dirname(serverSidePathToImport)
            module = self._importModuleFromDirectory(
                fullname, name, moduleDir, forceReload=self._reloadClasses)
            return module

        # First, we'll import the context's package.
        if os.sep != '/':
            fullname = fullname.replace(os.sep, '_')
        fullname = fullname.replace('/', '_')
        directory, contextDirName = os.path.split(contextPath)
        self._importModuleFromDirectory(
            fullname, contextDirName, directory or '.', isPackageDir=True)
        directory = contextPath

        # Now we'll break up the rest of the path into components.
        remainder = path[len(contextPath)+1:]
        if os.sep != '/':
            remainder = remainder.replace(os.sep, '/')
        remainder = remainder.split('/')

        # Import all subpackages of the context package
        for name in remainder[:-1]:
            fullname = f'{fullname}.{name}'
            self._importModuleFromDirectory(
                fullname, name, directory, isPackageDir=True)
            directory = os.path.join(directory, name)

        # Finally, import the module itself as though it was part of the
        # package or subpackage, even though it may be located somewhere else.
        moduleFileName = os.path.basename(serverSidePathToImport)
        moduleDir = os.path.dirname(serverSidePathToImport)
        name = os.path.splitext(moduleFileName)[0]
        fullname = f'{fullname}.{name}'
        module = self._importModuleFromDirectory(
            fullname, name, moduleDir, forceReload=self._reloadClasses)
        return module

    def _importModuleFromDirectory(
            self, fullModuleName, moduleName,
            directory, isPackageDir=False, forceReload=False):
        """Imports the given module from the given directory.

        fullModuleName should be the full dotted name that will be given
        to the module within Python. moduleName should be the name of the
        module in the filesystem, which may be different from the name
        given in fullModuleName. Returns the module object.
        If forceReload is True, then this reloads the module even if it
        has already been imported.

        If isPackageDir is True, then this function creates an empty
        __init__.py if that file doesn't already exist.
        """
        if debug:
            print(__file__, fullModuleName, moduleName, directory)
        module = sys.modules.get(fullModuleName)
        if module is not None and not forceReload:
            return module
        if isPackageDir:
            # check if __init__.py is in the directory
            packageDir = os.path.join(directory, moduleName)
            initPy = os.path.join(packageDir, '__init__.py')
            if (not os.path.exists(initPy) and
                    not os.path.exists(initPy + 'c')):
                # if it does not exist, make an empty one
                print(f"Creating __init__.py file at {packageDir!r}")
                try:
                    with open(initPy, 'w') as initPyFile:
                        initPyFile.write(
                            '# Auto-generated by Webware' + os.linesep)
                except Exception:
                    print("Error: __init__.py file could not be created.")
        spec = self._imp.findSpec(moduleName, directory, fullModuleName)
        module = self._imp.moduleFromSpec(spec)
        module.__donotreload__ = self._reloadClasses
        sys.modules[fullModuleName] = module
        return module

    def loadClass(self, transaction, path):
        """Load the appropriate class.

        Given a transaction and a path, load the class for creating these
        servlets. Caching, pooling, and threadsafeness are all handled by
        servletForTransaction. This method is not expected to be threadsafe.
        """
        raise AbstractError(self.__class__)

    # endregion Import

    # region Servlet Pool

    def servletForTransaction(self, transaction):
        """Return a new servlet that will handle the transaction.

        This method handles caching, and will call loadClass(trans, filepath)
        if no cache is found. Caching is generally controlled by servlets
        with the canBeReused() and canBeThreaded() methods.
        """
        request = transaction.request()
        path = request.serverSidePath()
        # Do we need to import/reimport the class
        # because the file changed on disk or isn't in cache?
        mtime = os.path.getmtime(path)
        if (path not in self._classCache
                or mtime != self._classCache[path]['mtime']):
            # Use a lock to prevent multiple simultaneous
            # imports of the same module:
            with self._importLock:
                if (path not in self._classCache
                        or mtime != self._classCache[path]['mtime']):
                    # pylint: disable = assignment-from-no-return
                    theClass = self.loadClass(transaction, path)
                    if self._cacheClasses:
                        self._classCache[path] = {
                            'mtime': mtime, 'class': theClass}
                else:
                    theClass = self._classCache[path]['class']
        else:
            theClass = self._classCache[path]['class']

        # Try to find a cached servlet of the correct class.
        # (Outdated servlets may have been returned to the pool after a new
        # class was imported, but we don't want to use an outdated servlet.)
        if path in self._threadsafeServletCache:
            servlet = self._threadsafeServletCache[path]
            if servlet.__class__ is theClass:
                return servlet
        else:
            while True:
                try:
                    servlet = self._servletPool[path].pop()
                except (KeyError, IndexError):
                    break
                else:
                    if servlet.__class__ is theClass:
                        servlet.open()
                        return servlet

        # Use a lock to prevent multiple simultaneous imports of the same
        # module. Note that (only) the import itself is already threadsafe.
        with self._importLock:
            mtime = os.path.getmtime(path)
            # pylint: disable = assignment-from-no-return
            if path not in self._classCache:
                self._classCache[path] = {
                    'mtime': mtime,
                    'class': self.loadClass(transaction, path)}
            elif mtime > self._classCache[path]['mtime']:
                self._classCache[path]['mtime'] = mtime
                self._classCache[path]['class'] = self.loadClass(
                    transaction, path)
            theClass = self._classCache[path]['class']
            if not self._cacheClasses:
                del self._classCache[path]

        # No adequate cached servlet exists, so create a new servlet instance
        servlet = theClass()
        servlet.setFactory(self)
        if servlet.canBeReused():
            if servlet.canBeThreaded():
                self._threadsafeServletCache[path] = servlet
            else:
                self._servletPool[path] = []
                servlet.open()
        return servlet

    def returnServlet(self, servlet):
        """Return servlet to the pool.

        Called by Servlet.close(), which returns the servlet
        to the servlet pool if necessary.
        """
        if (servlet.canBeReused() and not servlet.canBeThreaded()
                and self._cacheInstances):
            path = servlet.serverSidePath()
            self._servletPool[path].append(servlet)

    def flushCache(self):
        """Flush the servlet cache and start fresh.

        Servlets that are currently in the wild may find their way back
        into the cache (this may be a problem).
        """
        self._importLock.acquire()
        self._classCache = {}
        # We can't just delete all the lists, because returning
        # servlets expect it to exist.
        for key in self._servletPool:
            self._servletPool[key] = []
        self._threadsafeServletCache = {}
        self._importLock.release()

    # endregion Servlet Pool


class PythonServletFactory(ServletFactory):
    """The factory for Python servlets.

    This is the factory for ordinary Python servlets whose extensions
    are empty or .py. The servlets are unique per file since the file
    itself defines the servlet.
    """

    # region Info

    def uniqueness(self):
        return 'file'

    def extensions(self):
        # The extensions of ordinary Python servlets. Besides .py, we also
        # allow .pyc files as Python servlets, so that you can use servlets
        # in the production environment without the source code.
        # Otherwise they would be treated as ordinary files which might
        # become a security hole (though the standard configuration ignores
        # the .pyc files). If you use both extensions, make sure .py
        # comes before .pyc in the ExtensionCascadeOrder.
        return ['.py', '.pyc']

    # endregion Info

    # region Import

    def loadClass(self, transaction, path):
        # Import the module as part of the context's package
        module = self.importAsPackage(transaction, path)

        # The class name is expected to be the same as the servlet name:
        name = os.path.splitext(os.path.split(path)[1])[0]
        # Check whether such a class exists in the servlet module:
        if not hasattr(module, name):
            # If it does not exist, maybe the name has to be mangled.
            # Servlet names may have dashes or blanks in them, but classes not.
            # So we automatically translate dashes blanks to underscores:
            name = name.replace('-', '_').replace(' ', '_')
            # You may also have a servlet name that is a Python reserved word.
            # Automatically append an underscore in these cases:
            if iskeyword(name):
                name += '_'
            # If the mangled name does not exist either, report an error:
            if not hasattr(module, name):
                raise ValueError(
                    'Cannot find expected servlet class'
                    f' {name!r} in {path!r}.')
        # Pull the servlet class out of the module:
        theClass = getattr(module, name)
        if not (isinstance(theClass, object)
                and issubclass(theClass, Servlet)):
            raise TypeError(f'Expected a Servlet class: {theClass!r}')
        return theClass

    # endregion Import
