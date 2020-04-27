"""URLParser

URL parsing is done through objects which are subclasses of the `URLParser`
class. `Application` delegates most of the URL parsing to these objects.

Application has a single "root" URL parser, which is used to parse all URLs.
This parser then can pass the request on to other parsers, usually taking off
parts of the URL with each step.

This root parser is generally `ContextParser`, which is instantiated and set
up by `Application` (accessible through `Application.rootURLParser`).
"""

import os
import re
import sys

from collections import defaultdict
from urllib.parse import unquote
from warnings import warn

from HTTPExceptions import HTTPNotFound, HTTPMovedPermanently
from MiscUtils.ParamFactory import ParamFactory

debug = False

# Legal characters for use in a module name -- used when turning
# an entire path into a module name.
_moduleNameRE = re.compile('[^a-zA-Z_]')

_globalApplication = None


def application():
    """Returns the global Application."""
    return _globalApplication


class URLParser:
    """URLParser is the base class for all URL parsers.

    Though its functionality is sparse, it may be expanded in the future.
    Subclasses should implement a `parse` method, and may also want to
    implement an `__init__` method with arguments that control how the
    parser works (for instance, passing a starting path for the parser)

    The `parse` method is where most of the work is done. It takes two
    arguments -- the transaction and the portion of the URL that is still to
    be parsed. The transaction may (and usually is) modified along the way.
    The URL is passed through so that you can take pieces off the front,
    and then pass the reduced URL to another parser. The method should return
    a servlet (never None).

    If you cannot find a servlet, or some other (somewhat) expected error
    occurs, you should raise an exception. HTTPNotFound probably being the
    most interesting.
    """

    def findServletForTransaction(self, trans):
        """Returns a servlet for the transaction.

        This is the top-level entry point, below it `parse` is used.
        """
        # pylint: disable=no-member
        return self.parse(trans, trans.request().urlPath())


class ContextParser(URLParser):
    """Find the context of a request.

    ContextParser uses the ``Application.config`` context settings to find
    the context of the request.  It then passes the request to a FileParser
    rooted in the context path.

    The context is the first element of the URL, or if no context matches
    that then it is the ``default`` context (and the entire URL is passed
    to the default context's FileParser).

    There is generally only one ContextParser, which can be found as
    ``application.rootURLParser()``.
    """

    # region Init

    def __init__(self, app):
        """Create ContextParser.

        ContextParser is usually created by Application, which
        passes all requests to it.

        In __init__ we take the ``Contexts`` setting from
        Application.config and parse it slightly.
        """
        URLParser.__init__(self)
        # Need to set this here because we need this during initialization:
        self._app = app
        self._imp = app._imp
        # self._context will be a dictionary of context names and context
        # directories.  It is set by `addContext`.
        self._contexts = {}
        # add all contexts except the default, which we save until the end
        contexts = app.setting('Contexts')
        defaultContext = ''
        for name, path in contexts.items():
            path = os.path.normpath(path)  # for Windows
            if name == 'default':
                defaultContext = path
            else:
                name = '/'.join(p for p in name.split('/') if p)
                self.addContext(name, path)
        if not defaultContext:
            # If no default context has been specified, and there is a unique
            # context not built into Webware, use it as the default context.
            for name in contexts:
                if name in ('Admin', 'Examples', 'Testing'):
                    continue
                if defaultContext:
                    defaultContext = None
                    break
                defaultContext = name
            if not defaultContext:
                # otherwise, try using the following contexts if available
                for defaultContext in ('Default', 'Examples'):
                    if defaultContext in contexts:
                        break
                else:  # if not available, refuse the temptation to guess
                    raise KeyError("No default context has been specified.")
        if defaultContext in self._contexts:
            self._defaultContext = defaultContext
        else:
            for name, path in self._contexts.items():
                if defaultContext == path:
                    self._defaultContext = name
                    break
            else:
                self.addContext('default', defaultContext)
                self._defaultContext = 'default'

    # endregion Init

    # region Context handling

    def resolveDefaultContext(self, dest):
        """Find default context.

        Figure out if the default context refers to an existing context,
        the same directory as an existing context, or a unique directory.

        Returns the name of the context that the default context refers to,
        or 'default' if the default context is unique.
        """
        contexts = self._contexts
        if dest in contexts:
            # The default context refers to another context,
            # not a unique context.  Return the name of that context.
            return dest
        destPath = self.absContextPath(dest)
        for name, path in contexts.items():
            if name != 'default' and self.absContextPath(path) == destPath:
                # The default context has the same directory
                # as another context, so it's still not unique
                return name
        # The default context has no other name
        return 'default'

    def addContext(self, name, path):
        """Add a context to the system.

        The context will be imported as a package, going by `name`,
        from the given directory path. The directory doesn't have to match
        the context name.
        """
        if name == 'default':
            dest = self.resolveDefaultContext(name)
            self._defaultContext = dest
            if dest != 'default':
                # in this case default refers to an existing context, so
                # there's not much to do
                print('Default context aliases to:', dest)
                return

        if name in sys.modules:
            module = sys.modules[name]
        else:
            try:
                localDir, packageName = os.path.split(path)
                spec = self._imp.findSpec(packageName, localDir or '.')
                try:
                    module = self._imp.moduleFromSpec(spec)
                except ImportError as e:
                    # Maybe this happened because it had been forgotten
                    # to add the __init__.py file. So we try to create one:
                    if os.path.exists(path):
                        initPy = os.path.join(path, '__init__.py')
                        if (not os.path.exists(initPy) and
                                not os.path.exists(initPy + 'c')):
                            print("Creating __init__.py file"
                                  f" for context {name!r}")
                            try:
                                with open(initPy, 'w') as initPyFile:
                                    initPyFile.write(
                                        '# Auto-generated by Webware' +
                                        os.linesep)
                            except Exception:
                                print("Error: __init__.py file"
                                      " could not be created.")
                            else:
                                module = self._imp.moduleFromSpec(spec)
                                e = None
                    if e:
                        raise
                else:
                    sys.modules[name] = module
            except ImportError as e:
                error = str(e) or 'Could not import package'
                print(f'Error loading context: {name}: {error}: dir={path}')
                return

        if hasattr(module, 'contextInitialize'):
            result = module.contextInitialize(
                application(),
                os.path.normpath(os.path.join(os.getcwd(), path)))
            if result is not None and 'ContentLocation' in result:
                path = result['ContentLocation']

        print(f'Loading context: {name} at {path}')
        self._contexts[name] = path

    def absContextPath(self, path):
        """Get absolute context path.

        Resolves relative paths, which are assumed to be relative to the
        Application's serverSidePath (the working directory).
        """
        if os.path.isabs(path):
            return path
        return self._app.serverSidePath(path)

    # endregion Context handling

    # region Parsing

    def parse(self, trans, requestPath):
        """Parse request.

        Get the context name, and dispatch to a FileParser rooted
        in the context's path.

        The context name and file path are stored in the request (accessible
        through `Request.serverSidePath` and `Request.contextName`).
        """
        # This is a hack... should probably go in the Transaction class:
        trans._fileParserInitSeen = defaultdict(set)
        # If there is no path, redirect to the root path:
        req = trans.request()
        if not requestPath:
            p = req.servletPath() + '/'
            q = req.queryString()
            if q:
                p += "?" + q
            raise HTTPMovedPermanently(location=p)
        # Determine the context name:
        context = [p for p in requestPath.split('/') if p]
        if requestPath.endswith('/'):
            context.append('')
        parts = []
        while context:
            contextName = '/'.join(context)
            if contextName in self._contexts:
                break
            parts.insert(0, context.pop())
        if context:
            if parts:
                parts.insert(0, '')
                requestPath = '/'.join(parts)
            else:
                requestPath = ''
        else:
            contextName = self._defaultContext
        context = self._contexts[contextName]
        req._serverSideContextPath = context
        req._contextName = contextName
        fp = FileParser(context)
        return fp.parse(trans, requestPath)


class _FileParser(URLParser):
    """Parse requests to the filesystem.

    FileParser dispatches to servlets in the filesystem, as well as providing
    hooks to override the FileParser.

    FileParser objects are threadsafe. A factory function is used to cache
    FileParser instances, so for any one path only a single FileParser instance
    will exist.  The `_FileParser` class is the real class, and `FileParser` is
    a factory that either returns an existent _FileParser object, or creates a
    new one if none exists.

    FileParser uses several settings from ``Application.config``, which are
    persistent over the life of the application. These are set up in the
    function `initApp`, as class variables. They cannot be set when the module
    is loaded, because the Application is not yet set up, so `initApp` is
    called in `Application.__init__`.
    """

    # compiled modules with these extensions will be loaded
    # even if no source file exists
    _byteCodeExtensions = ['opt-2.pyc']

    # endregion Parsing

    # region Init

    def __init__(self, path):
        """Create a FileParser.

        Each parsed directory has a FileParser instance associated with it
        (``self._path``).
        """
        URLParser.__init__(self)
        self._path = path
        self._initModule = None

    # endregion Init

    # region Parsing

    def parse(self, trans, requestPath):
        """Return the servlet.

        __init__ files will be used for various hooks
        (see `parseInit` for more).

        If the next part of the URL is a directory, it calls
        ``FileParser(dirPath).parse(trans, restOfPath)`` where ``restOfPath``
        is `requestPath` with the first section of the path removed (the part
        of the path that this FileParser just handled).

        This uses `fileNamesForBaseName` to find files in its directory.
        That function has several functions to define what files are ignored,
        hidden, etc.  See its documentation for more information.
        """
        if debug:
            print(f"FP({self._path!r}) parses {requestPath!r}")

        req = trans.request()

        # First decode the URL, since we are dealing with filenames here:
        # We must use unquote instead of unquote_plus, because decoding
        # the plus sign should only happen for the query string.
        requestPath = unquote(requestPath)

        result = self.parseInit(trans, requestPath)
        if result is not None:
            return result

        if not requestPath or requestPath == '/':
            return self.parseIndex(trans, requestPath)

        if not requestPath.startswith('/'):
            raise HTTPNotFound(f"Invalid path info: {requestPath}")

        parts = requestPath[1:].split('/', 1)
        nextPart = parts[0]
        restPart = '/' + parts[1] if len(parts) > 1 else ''

        baseName = os.path.join(self._path, nextPart)
        if restPart and not self._extraPathInfo:
            names = [baseName]
        else:
            names = self.filenamesForBaseName(baseName)

        if len(names) > 1:
            warn("More than one file matches"
                 f"{requestPath} in {self._path}: {names}")
            raise HTTPNotFound("Page is ambiguous")
        if not names:
            return self.parseIndex(trans, requestPath)

        name = names[0]
        if os.path.isdir(name):
            # directories are dispatched to FileParsers
            # rooted in that directory
            fp = FileParser(name)
            return fp.parse(trans, restPart)

        req._extraURLPath = restPart

        if not self._extraPathInfo and restPart:
            raise HTTPNotFound(f"Invalid extra path info: {restPart}")

        req._serverSidePath = name

        return ServletFactoryManager.servletForFile(trans, name)

    def filenamesForBaseName(self, baseName):
        """Find all files for a given base name.

        Given a path, like ``/a/b/c``, searches for files in ``/a/b``
        that start with ``c``.  The final name may include an extension,
        which is less ambiguous; though if you ask for file.html,
        and file.html.py exists, that file will be returned.

        The files are filtered according to the settings ``FilesToHide``,
        ``FilesToServe``, ``ExtensionsToIgnore`` and ``ExtensionsToServe``.
        See the shouldServeFile() method for details on these settings.

        All files that start with the given base name are returned
        as a list. When the base name itself is part of the list or
        when extensions are prioritized and such an extension is found
        in the list, then the list will be reduced to only that entry.

        Some settings are used to control the prioritization of filenames.
        All settings are in ``Application.config``:

        UseCascadingExtensions:
            If true, then extensions will be prioritized.  So if
            extension ``.tmpl`` shows up in ExtensionCascadeOrder
            before ``.html``, then even if filenames with both
            extensions exist, only the .tmpl file will be returned.
        ExtensionCascadeOrder:
            A list of extensions, ordered by priority.
        """
        if '*' in baseName:
            return []

        fileStart = os.path.basename(baseName)
        dirName = os.path.dirname(baseName)
        filenames = []
        for filename in os.listdir(dirName):
            if filename.startswith('.'):
                continue
            if filename == fileStart:
                if self.shouldServeFile(filename):
                    return [os.path.join(dirName, filename)]
            elif (filename.startswith(fileStart)
                  and os.path.splitext(filename)[0] == fileStart):
                if self.shouldServeFile(filename):
                    filenames.append(os.path.join(dirName, filename))

        if self._useCascading and len(filenames) > 1:
            for extension in self._cascadeOrder:
                if baseName + extension in filenames:
                    return [baseName + extension]

        return filenames

    def shouldServeFile(self, filename):
        """Check if the file with the given filename should be served.

        Some settings are used to control the filtering of filenames.
        All settings are in ``Application.config``:

        FilesToHide:
            These files will be ignored, and even given a full
            extension will not be used.  Takes a glob.
        FilesToServe:
            If set, *only* files matching these globs will be
            served, all other files will be ignored.
        ExtensionsToIgnore:
            Files with these extensions will be ignored, but if a
            complete filename (with extension) is given the file
            *will* be served (unlike FilesToHide).  Extensions are
            in the form ``".py"``
        ExtensionsToServe:
            If set, only files with these extensions will be
            served.  Like FilesToServe, only doesn't use globs.
        """
        ext = os.path.splitext(filename)[1]
        if ext in self._toIgnore:
            return False
        if self._toServe and ext not in self._toServe:
            return False
        for regex in self._filesToHideRegexes:
            if regex.match(filename):
                return False
        if self._filesToServeRegexes:
            for regex in self._filesToServeRegexes:
                if regex.match(filename):
                    break
            else:
                return False
        return True

    def parseIndex(self, trans, requestPath):
        """Return index servlet.

        Return the servlet for a directory index (i.e., ``Main`` or
        ``index``).  When `parse` encounters a directory and there's nothing
        left in the URL, or when there is something left and no file matches
        it, then it will try `parseIndex` to see if there's an index file.

        That means that if ``/a/b/c`` is requested, and in ``/a`` there's no
        file or directory matching ``b``, then it'll look for an index file
        (like ``Main.py``), and that servlet will be returned. In fact, if
        no ``a`` was found, and the default context had an index (like
        ``index.html``) then that would be called with ``/a/b/c`` as
        `HTTPRequest.extraURLPath`.  If you don't want that to occur, you
        should raise an HTTPNotFound in your no-extra-url-path-taking servlets.

        The directory names are based off the ``Application.config`` setting
        ``DirectoryFile``, which is a list of base names, by default
        ``["Main", "index", "main", "Index"]``, which are searched in order.
        A file with any extension is allowed, so the index can be an HTML file,
        a PSP file, a Python servlet, etc.
        """
        req = trans.request()
        # If requestPath is empty, then we're missing the trailing slash:
        if not requestPath:
            p = req.serverURL() + '/'
            q = req.queryString()
            if q:
                p += "?" + q
            raise HTTPMovedPermanently(location=p)
        if requestPath == '/':
            requestPath = ''
        for directoryFile in self._directoryFile:
            basename = os.path.join(self._path, directoryFile)
            names = self.filenamesForBaseName(basename)
            if len(names) > 1 and self._useCascading:
                for ext in self._cascadeOrder:
                    if basename + ext in names:
                        names = [basename + ext]
                        break
            if len(names) > 1:
                warn("More than one file matches the index file"
                     f" {directoryFile} in {self._path}: {names}")
                raise HTTPNotFound("Index page is ambiguous")
            if names:
                if requestPath and not self._extraPathInfo:
                    raise HTTPNotFound
                req._serverSidePath = names[0]
                req._extraURLPath = requestPath
                return ServletFactoryManager.servletForFile(trans, names[0])
        raise HTTPNotFound("Index page not found")

    def initModule(self):
        """Get the __init__ module object for this FileParser's directory."""
        path = self._path
        # if this directory is a context, return the context package
        for context, contextDir in self._app.contexts().items():
            if contextDir == path:
                # avoid reloading of the context package
                return sys.modules.get(context)
        try:
            spec = self._imp.findSpec('__init__', path)
            self._imp.moduleFromSpec(spec)
        except (ImportError, TypeError):
            pass

    def parseInit(self, trans, requestPath):
        """Parse the __init__ file.

        Returns the resulting servlet, or None if no __init__ hooks were found.

        Hooks are put in by defining special functions or objects in your
        __init__, with specific names:

        `urlTransactionHook`:
            A function that takes one argument (the transaction).
            The return value from the function is ignored.  You
            can modify the transaction with this function, though.

        `urlRedirect`:
            A dictionary.  Keys in the dictionary are source
            URLs, the value is the path to redirect to, or a
            `URLParser` object to which the transaction should
            be delegated.

            For example, if the URL is ``/a/b/c``, and we've already
            parsed ``/a`` and are looking for ``b/c``, and we fine
            `urlRedirect`` in a.__init__, then we'll look for a key
            ``b`` in the dictionary.  The value will be a directory
            we should continue to (say, ``/destpath/``).  We'll
            then look for ``c`` in ``destpath``.

            If a key '' (empty string) is in the dictionary, then
            if no more specific key is found all requests will
            be redirected to that path.

            Instead of a string giving a path to redirect to, you
            can also give a URLParser object, so that some portions
            of the path are delegated to different parsers.

            If no matching key is found, and there is no '' key,
            then parsing goes on as usual.

        `SubParser`:
            This should be a class object.  It will be instantiated,
            and then `parse` will be called with it, delegating to
            this instance.  When instantiated, it will be passed
            *this* FileParser instance; the parser can use this to
            return control back to the FileParser after doing whatever
            it wants to do.

            You may want to use a line like this to handle the names::

                from ParserX import ParserX as SubParser

        `urlParser`:
            This should be an already instantiated URLParser-like
            object.  `parse(trans, requestPath)` will be called
            on this instance.

        `urlParserHook`:
            Like `urlParser`, except the method
            `parseHook(trans, requestPath, fileParser)` will
            be called, where fileParser is this FileParser instance.

        `urlJoins`:
            Either a single path, or a list of paths.  You can also
            use URLParser objects, like with `urlRedirect`.

            Each of these paths (or parsers) will be tried in
            order.  If it raises HTTPNotFound, then the next path
            will be tried, ending with the current path.

            Paths are relative to the current directory.  If you
            don't want the current directory to be a last resort,
            you can include '.' in the joins.
        """
        if self._initModule is None:
            self._initModule = self.initModule()
        mod = self._initModule

        seen = trans._fileParserInitSeen[self._path]

        if ('urlTransactionHook' not in seen
                and hasattr(mod, 'urlTransactionHook')):
            seen.add('urlTransactionHook')
            mod.urlTransactionHook(trans)

        if 'urlRedirect' not in seen and hasattr(mod, 'urlRedirect'):
            seen.add('urlRedirect')
            try:
                nextPart, restPath = requestPath[1:].split('/', 1)
                restPath = '/' + restPath
            except ValueError:
                nextPart = requestPath[1:]
                restPath = ''
            if nextPart in mod.urlRedirect:
                redirectTo = mod.urlRedirect[nextPart]
                redirectPath = restPath
            elif '' in mod.urlRedirect:
                redirectTo = mod.urlRedirect['']
                redirectPath = restPath
            else:
                redirectTo = None
            if redirectTo:
                if isinstance(redirectTo, str):
                    fp = FileParser(os.path.join(self._path, redirectTo))
                else:
                    fp = redirectTo
                return fp.parse(trans, redirectPath)

        if 'SubParser' not in seen and hasattr(mod, 'SubParser'):
            seen.add('SubParser')
            parser = mod.SubParser(self)
            return parser.parse(trans, requestPath)

        if 'urlParser' not in seen and hasattr(mod, 'urlParser'):
            seen.add('urlParser')
            parser = mod.urlParser
            return parser.parse(trans, requestPath)

        if 'urlParserHook' not in seen and hasattr(mod, 'urlParserHook'):
            seen.add('urlParserHook')
            parser = mod.urlParserHook
            return parser.parseHook(trans, requestPath, self)

        if 'urlJoins' not in seen and hasattr(mod, 'urlJoins'):
            seen.add('urlJoins')
            joinPath = mod.urlJoins
            if isinstance(joinPath, str):
                joinPath = [joinPath]
            for path in joinPath:
                path = os.path.join(self._path, path)
                if isinstance(path, str):
                    parser = FileParser(os.path.join(self._path, path))
                else:
                    parser = path
                try:
                    return parser.parse(trans, requestPath)
                except HTTPNotFound:
                    pass

        return None

    # endregion Parsing


FileParser = ParamFactory(_FileParser)


class URLParameterParser(URLParser):
    """Strips named parameters out of the URL.

    E.g. in ``/path/SID=123/etc`` the ``SID=123`` will be removed from the URL,
    and a field will be set in the request (so long as no field by that name
    already exists -- if a field does exist the variable is thrown away).
    These are put in the place of GET or POST variables.

    It should be put in an __init__, like::

        from URLParser import URLParameterParser
        urlParserHook = URLParameterParser()

    Or (slightly less efficient):

        from URLParser import URLParameterParser as SubParser
    """

    # region Init

    def __init__(self, fileParser=None):
        self._fileParser = fileParser

    # endregion Init

    # region Parsing

    def parse(self, trans, requestPath):
        """Delegates to `parseHook`."""
        return self.parseHook(trans, requestPath, self._fileParser)

    @staticmethod
    def parseHook(trans, requestPath, hook):
        """Munges the path.

        The `hook` is the FileParser object that originally called this --
        we just want to strip stuff out of the URL and then give it back to
        the FileParser instance, which can actually find the servlet.
        """
        parts = requestPath.split('/')
        result = []
        req = trans.request()
        for part in parts:
            if '=' in part:
                name, value = part.split('=', 1)
                if not req.hasField(name):
                    req.setField(name, value)
            else:
                result.append(part)
        return hook.parse(trans, '/'.join(result))

    # endregion Parsing


class ServletFactoryManagerClass:
    """Manage servlet factories.

    This singleton (called `ServletFactoryManager`) collects and manages
    all the servlet factories that are installed.

    See `addServletFactory` for adding new factories, and `servletForFile`
    for getting the factories back.
    """

    # region Init

    def __init__(self):
        self.reset()

    def reset(self):
        self._factories = []
        self._factoryExtensions = {}

    # endregion Init

    # region Manager

    def addServletFactory(self, factory):
        """Add a new servlet factory.

        Servlet factories can add themselves with::

            ServletFactoryManager.addServletFactory(factory)

        The factory must have an `extensions` method, which should
        return a list of extensions that the factory handles (like
        ``['.ht']``).  The special extension ``.*`` will match any
        file if no other factory is found.  See `ServletFactory`
        for more information.
        """

        self._factories.append(factory)
        for ext in factory.extensions():
            if ext in self._factoryExtensions:
                raise KeyError(
                    f"Extension {ext!r} for factory {factory.__name__}"
                    " was already used by factory"
                    f" {self._factoryExtensions[ext].__name__}")
            self._factoryExtensions[ext] = factory

    def factoryForFile(self, path):
        """Get a factory for a filename."""
        ext = os.path.splitext(path)[1]
        if ext in self._factoryExtensions:
            return self._factoryExtensions[ext]
        if '.*' in self._factoryExtensions:
            return self._factoryExtensions['.*']
        raise HTTPNotFound

    def servletForFile(self, trans, path):
        """Get a servlet for a filename and transaction.

        Uses `factoryForFile` to find the factory, which
        creates the servlet.
        """
        factory = self.factoryForFile(path)
        return factory.servletForTransaction(trans)

    # endregion Manager


ServletFactoryManager = ServletFactoryManagerClass()


# region Global Init

def initApp(app):
    """Initialize the application.

    Installs the proper servlet factories, and gets some settings from
    Application.config. Also saves the application in _globalApplication
    for future calls to the application() function.

    This needs to be called before any of the URLParser-derived classes
    are instantiated.
    """
    global _globalApplication
    _globalApplication = app
    from UnknownFileTypeServlet import UnknownFileTypeServletFactory
    from ServletFactory import PythonServletFactory

    ServletFactoryManager.reset()
    for factory in [UnknownFileTypeServletFactory, PythonServletFactory]:
        ServletFactoryManager.addServletFactory(factory(app))

    initParser(app)


def initParser(app):
    """Initialize the FileParser Class."""
    cls = _FileParser
    cls._app = app
    cls._imp = app._imp
    cls._contexts = app.contexts
    cls._filesToHideRegexes = []
    cls._filesToServeRegexes = []
    from fnmatch import translate as fnTranslate
    for pattern in app.setting('FilesToHide'):
        cls._filesToHideRegexes.append(re.compile(fnTranslate(pattern)))
    for pattern in app.setting('FilesToServe'):
        cls._filesToServeRegexes.append(re.compile(fnTranslate(pattern)))
    cls._toIgnore = app.setting('ExtensionsToIgnore')
    cls._toServe = app.setting('ExtensionsToServe')
    cls._useCascading = app.setting('UseCascadingExtensions')
    cls._cascadeOrder = app.setting('ExtensionCascadeOrder')
    cls._directoryFile = app.setting('DirectoryFile')
    cls._extraPathInfo = app.setting('ExtraPathInfo')

# endregion Global Init
