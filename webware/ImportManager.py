"""ImportManager

Manages imported modules and protects against concurrent imports.

Keeps lists of all imported Python modules and templates as well as other
config files used by Webware for Python. Modules which are not directly
imported can be monitored using hupper. This can be used to detect changes in
source files, templates or config files in order to reload them automatically.
"""


import sys
import warnings

from os.path import getmtime, isfile, join
from importlib.util import module_from_spec, spec_from_file_location
from importlib.machinery import (
    ModuleSpec, SourceFileLoader, SourcelessFileLoader)


class ImportManager:
    """The import manager.

    Keeps track of the Python modules and other system files that have been
    imported and are used by Webware.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Create ImportManager as a singleton."""
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize import manager."""
        self._fileList = {}
        self._moduleFiles = {}
        self._notifyHook = None
        self._reloader = self.getReloader()

    def getReloader(self):
        """Get the current reloader if the application is monitored."""
        reloader = None
        with warnings.catch_warnings():
            # ignore deprecation warnings from hupper
            warnings.filterwarnings('ignore', category=DeprecationWarning)
            try:
                import hupper
            except ImportError:
                pass
            else:
                if hupper.is_active():
                    try:
                        reloader = hupper.get_reloader()
                    except RuntimeError:
                        pass
        if reloader:
            print('Application is monitored for reloading.')
            print()
        return reloader

    def moduleFromSpec(self, spec):
        """Load the module with the given module spec."""
        if not spec or not isinstance(spec, ModuleSpec):
            raise TypeError(f'Invalid spec: {spec!r}')
        try:
            module = module_from_spec(spec)
        except Exception:
            # Also record file paths which weren't successfully loaded, which
            # may happen due to a syntax error in a servlet, because we also
            # want to know when such a file is modified:
            if spec.origin:
                self.recordFile(spec.origin)
            raise
        self.recordModule(module)
        spec.loader.exec_module(module)
        return module

    def findSpec(self, name, path, fullModuleName=None):
        """Find the module spec for the given name at the given path."""
        if not name or not isinstance(name, str):
            raise TypeError(f'Invalid name: {name!r}')
        if not path or not isinstance(path, str):
            raise TypeError(f'Invalid path: {path!r}')

        # find package
        packageDirectory = join(path, name)
        packageFileName = '__init__.py'
        filePath = join(packageDirectory, packageFileName)
        if isfile(filePath):
            return spec_from_file_location(name, filePath)

        # find package as byte code without source
        filePath += 'c'
        if isfile(filePath):
            return spec_from_file_location(name, filePath)

        # find module
        fileName = f'{name}.py'
        filePath = join(path, fileName)
        if isfile(filePath):
            if fullModuleName:
                name = fullModuleName
            loader = SourceFileLoader(name, filePath)
            return spec_from_file_location(name, filePath, loader=loader)

        # find module as optimized byte code without source
        filePath += 'c'
        if isfile(filePath):
            loader = SourcelessFileLoader(name, filePath)
            return spec_from_file_location(name, filePath, loader=loader)

        raise ImportError(f'No module named {name!r}')

    def fileList(self, update=True):
        """Return the list of tracked files."""
        if update:
            # Update list of files of imported modules
            moduleNames = [modname for modname in sys.modules
                           if modname not in self._moduleFiles]
            if moduleNames:
                self.recordModules(moduleNames)
        return self._fileList

    def notifyOfNewFiles(self, hook):
        """Register notification hook.

        Called by someone else to register that they'd like to know
        when a new file is imported.
        """
        self._notifyHook = hook

    def watchFile(self, path, moduleName=None, getmtime=getmtime):
        """Add more files to watch without importing them."""
        mtime = getmtime(path)
        self._fileList[path] = mtime
        if moduleName:
            self._moduleFiles[moduleName] = path
        # send notification that this file was imported
        if self._notifyHook:
            self._notifyHook(path, mtime)
        # let reloader know that this was imported
        if self._reloader:
            self._reloader.watch_files([path])

    def recordModule(self, module, isfile=isfile):
        """Record a module."""
        moduleName = getattr(module, '__name__', None)
        if not moduleName or moduleName not in sys.modules:
            return
        fileList = self._fileList
        # __orig_file__ is used for PSP and Cheetah templates; we want
        # to record the source filenames, not the auto-generated modules:
        f = getattr(module, '__orig_file__', None)
        if f and f not in fileList:
            try:
                if isfile(f):
                    self.watchFile(f, moduleName)
            except OSError:
                pass
        else:
            f = getattr(module, '__file__', None)
            if f and f not in fileList:
                # record the .py file corresponding to each .pyc
                if f[-4:].lower() == '.pyc':
                    f = f[:-1]
                try:
                    if isfile(f):
                        self.watchFile(f, moduleName)
                    else:
                        self.watchFile(join(f, '__init__.py'))
                except OSError:
                    pass

    def recordModules(self, moduleNames=None):
        """Record a list of modules (or all modules)."""
        if moduleNames is None:
            moduleNames = sys.modules
        for modname in moduleNames:
            mod = sys.modules[modname]
            self.recordModule(mod)

    def recordFile(self, filename, isfile=isfile):
        """Record a file."""
        if isfile(filename):
            self.watchFile(filename)

    def fileUpdated(self, filename, update=True, getmtime=getmtime):
        """Check whether file has been updated."""
        fileList = self.fileList(update)
        try:
            oldTime = fileList[filename]
        except KeyError:
            return True
        try:
            newTime = getmtime(filename)
        except OSError:
            return True
        if oldTime >= newTime:
            return False
        fileList[filename] = newTime
        # Note that the file list could be changed while running this
        # method in a monitor thread, so we don't use iteritems() here:
        for moduleName, moduleFile in self._moduleFiles.items():
            if moduleFile == filename:
                module = sys.modules.get(moduleName)
                return not module or not getattr(
                    module, '__donotreload__', False)
        return True  # it's not a module, we must reload

    def updatedFile(self, update=True, getmtime=getmtime):
        """Check whether one of the files has been updated."""
        fileList = self.fileList(update)
        for filename, oldTime in list(fileList.items()):
            try:
                newTime = getmtime(filename)
            except OSError:
                return filename
            if oldTime >= newTime:
                continue
            fileList[filename] = newTime
            for moduleName, moduleFile in self._moduleFiles.items():
                if moduleFile == filename:
                    module = sys.modules.get(moduleName)
                    if module and getattr(module, '__donotreload__', False):
                        break
                    return filename  # it's a module that needs to be reloaded
            else:
                return filename  # it's not a module, we must reload

    def delModules(self, includePythonModules=False, excludePrefixes=None):
        """Delete imported modules.

        Deletes all the modules that have been imported unless they are part
        of Webware. This can be used to support auto reloading.
        """
        moduleFiles = self._moduleFiles
        fileList = self._fileList
        for modname in moduleFiles:
            if modname == __name__:
                continue
            filename = self._moduleFiles[modname]
            if not includePythonModules:
                if not filename or filename.startswith(sys.prefix):
                    continue
            for prefix in excludePrefixes or []:
                if modname.startswith(prefix):
                    break
            else:
                try:
                    del sys.modules[modname]
                except KeyError:
                    pass
                try:
                    del moduleFiles[modname]
                except KeyError:
                    pass
                try:
                    del fileList[filename]
                except KeyError:
                    pass
