"""Servlet factory for unknown file types."""

import os

from mimetypes import guess_type

import HTTPExceptions

from HTTPServlet import HTTPServlet
from MiscUtils.Configurable import Configurable
from ServletFactory import ServletFactory

debug = False


try:
    from mimetypes import init as init_mimetypes
except ImportError:
    pass
else:  # workaround for Python issue #5853
    init_mimetypes()


class UnknownFileTypeServletFactory(ServletFactory):
    """The servlet factory for unknown file types.

    I.e. all files other than .py, .psp and the other types we support.
    """

    def uniqueness(self):
        return 'file'

    def extensions(self):
        return ['.*']

    def servletForTransaction(self, transaction):
        return UnknownFileTypeServlet(transaction.application())

    def flushCache(self):
        pass


# A cache of the files served up by UnknownFileTypeServlet cached by
# absolute, server side path. Each content is another dictionary with keys:
# content, mimeType, mimeEncoding.
# Previously, this content was stored directly in the attributes of the
# UnknownFileTypeServlets, but with that approach subclasses cannot
# dynamically serve content from different locations.
fileCache = {}


class UnknownFileTypeServlet(HTTPServlet, Configurable):
    """Servlet for unknown file types.

    Normally this class is just a "private" utility class for Webware's
    purposes. However, you may find it useful to subclass on occasion,
    such as when the server side file path is determined by something
    other than a direct correlation to the URL. Here is such an example:

    from UnknownFileTypeServlet import UnknownFileTypeServlet
    import os

    class Image(UnknownFileTypeServlet):

        imageDir = '/var/images'

        def filename(self, trans):
            filename = trans.request().field('i')
            filename = os.path.join(self.imageDir, filename)
            return filename
    """

    # region Candidates for subclass overrides

    def filename(self, trans):
        """Return the filename to be served.

        A subclass could override this in order to serve files from other
        disk locations based on some logic.
        """
        filename = getattr(self, '_serverSideFilename', None)
        if filename is None:
            filename = trans.request().serverSidePath()
            self._serverSideFilename = filename  # cache it
        return filename

    def shouldCacheContent(self):
        """Return whether the content should be cached or not.

        Returns a boolean that controls whether or not the content served
        through this servlet is cached. The default behavior is to return
        the CacheContent setting. Subclasses may override to always True
        or False, or incorporate some other logic.
        """
        return self.setting('CacheContent')

    # endregion Candidates for subclass overrides

    # region Init et al

    def __init__(self, application):
        HTTPServlet.__init__(self)
        Configurable.__init__(self)
        self._application = application

    def defaultConfig(self):
        """Get the default config.

        Taken from Application's 'UnknownFileTypes' default setting.
        """
        return self._application.defaultConfig()['UnknownFileTypes']

    def userConfig(self):
        """Get the user config.

        Taken from Application's 'UnknownFileTypes' user setting.
        """
        return self._application.userConfig().get('UnknownFileTypes', {})

    def configFilename(self):
        return self._application.configFilename()

    def canBeReused(self):
        return self.setting('ReuseServlets')

    @staticmethod
    def validTechniques():
        return ['serveContent', 'redirectSansScript']

    def respondToGet(self, trans):
        """Respond to GET request.

        Responds to the transaction by invoking self.foo() for foo is
        specified by the 'Technique' setting.
        """
        technique = self.setting('Technique')
        if technique == 'redirectSansAdapter':
            oldTechnique, technique = technique, 'redirectSansScript'
            print(f'The {oldTechnique!r} technique is deprecated,'
                  f' please use {technique!r} instead')
        if technique not in self.validTechniques():
            raise AttributeError(f'Invalid technique: {technique!r}')
        method = getattr(self, technique)
        method(trans)

    respondToHead = respondToGet

    def respondToPost(self, trans):
        """Respond to POST request.

        Invoke self.respondToGet().

        Since posts are usually accompanied by data, this might not be the
        best policy. However, a POST would most likely be for a CGI, which
        currently no one is mixing in with their Webware-based web sites.
        """
        self.respondToGet(trans)

    @staticmethod
    def redirectSansScript(trans):
        """Redirect to web server.

        Sends a redirect to a URL that doesn't contain the script name.
        Under the right configuration, this will cause the web server to
        then be responsible for the URL rather than the WSGI server.
        Keep in mind that links off the target page will *not* include
        the script name in the URL.
        """
        request = trans.request()
        newURL = os.path.split(request.scriptName())[0] + request.pathInfo()
        newURL = newURL.replace('//', '/')
        trans.response().sendRedirect(newURL)

    def lastModified(self, trans):
        try:
            return os.path.getmtime(self.filename(trans))
        except OSError:
            return None

    def serveContent(self, trans):
        response = trans.response()

        maxCacheContentSize = self.setting('MaxCacheContentSize')
        readBufferSize = self.setting('ReadBufferSize')

        # start sending automatically
        response.streamOut().setAutoCommit()

        filename = self.filename(trans)
        try:
            f = open(filename, 'rb')
        except IOError as e:
            raise HTTPExceptions.HTTPNotFound from e

        stat = os.fstat(f.fileno())
        fileSize, mtime = stat[6], stat[8]

        if debug:
            print('>> UnknownFileType.serveContent()')
            print('>> filename =', filename)
            print('>> size=', fileSize)
        fileDict = fileCache.get(filename)
        if fileDict is not None and mtime != fileDict['mtime']:
            # Cache is out of date; clear it.
            if debug:
                print('>> changed, clearing cache')
            del fileCache[filename]
            fileDict = None
        if fileDict is None:
            if debug:
                print('>> not found in cache')
            mimeType, mimeEncoding = guess_type(filename, False)
            if mimeType is None:
                mimeType, mimeEncoding = 'application/octet-stream', None
        else:
            mimeType = fileDict['mimeType']
            mimeEncoding = fileDict['mimeEncoding']
        response.setHeader('Content-Type', mimeType)
        response.setHeader('Content-Length', str(fileSize))
        if mimeEncoding:
            response.setHeader('Content-Encoding', mimeEncoding)
        if trans.request().method() == 'HEAD':
            f.close()
            return
        if (fileDict is None and self.setting('ReuseServlets')
                and self.shouldCacheContent()
                and fileSize < maxCacheContentSize):
            if debug:
                print('>> caching')
            fileDict = dict(
                content=f.read(),
                mimeType=mimeType, mimeEncoding=mimeEncoding,
                mtime=mtime, size=fileSize, filename=filename)
            fileCache[filename] = fileDict
        if fileDict is not None:
            if debug:
                print('>> sending content from cache')
            response.write(fileDict['content'])
        else:  # too big or not supposed to cache
            if debug:
                print('>> sending directly')
            numBytesSent = 0
            while numBytesSent < fileSize:
                data = f.read(min(fileSize-numBytesSent, readBufferSize))
                if data == '':
                    break  # unlikely, but safety first
                response.write(data)
                numBytesSent += len(data)
        f.close()

    # endregion Init et al
