"""This module handles requests from the application for PSP pages.

Copyright (c) by Jay Love, 2000 (mailto:jsliv@jslove.org)

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation or portions thereof, including modifications,
that you make.
"""

import sys
from os import listdir, unlink, utime
from os.path import (
    getatime, getmtime, exists, isdir, isfile, join, normcase, splitdrive)
from shutil import rmtree
from string import digits, ascii_letters

from ServletFactory import ServletFactory
from . import Context, PSPCompiler


class PSPServletFactory(ServletFactory):
    """Servlet Factory for PSP files."""

    def __init__(self, application):
        ServletFactory.__init__(self, application)
        self._cacheDir = join(application._cacheDir, 'PSP')
        sys.path.append(self._cacheDir)
        self._cacheClassFiles = self._cacheClasses
        t = ['_'] * 256
        for c in digits + ascii_letters:
            t[ord(c)] = c
        self._classNameTrans = ''.join(t)
        setting = application.setting
        self._extensions = setting('ExtensionsForPSP', ['.psp'])
        self._fileEncoding = setting('PSPFileEncoding', None)
        if setting('ClearPSPCacheOnStart', False):
            self.clearFileCache()
        self._recordFile = application._imp.recordFile

    def uniqueness(self):
        return 'file'

    def extensions(self):
        return self._extensions

    def fileEncoding(self):
        """Return the file encoding used in PSP files."""
        return self._fileEncoding

    def flushCache(self):
        """Clean out the cache of classes in memory and on disk."""
        ServletFactory.flushCache(self)
        self.clearFileCache()

    def clearFileCache(self):
        """Clear class files stored on disk."""
        cacheDir = self._cacheDir
        for filename in listdir(cacheDir):
            path = join(cacheDir, filename)
            if isfile(path):  # remove the source files
                unlink(path)
            elif isdir(path):  # also remove the __pycache__
                rmtree(path)

    def computeClassName(self, pageName):
        """Generates a (hopefully) unique class/file name for each PSP file.

        Argument: pageName: the path to the PSP source file
        Returns: a unique name for the class generated fom this PSP source file
        """
        # Compute class name by taking the normalized path and substituting
        # underscores for all non-alphanumeric characters:
        normName = normcase(splitdrive(pageName)[1])
        return normName.translate(self._classNameTrans)

    def loadClassFromFile(self, transaction, fileName, className):
        """Create an actual class instance.

        The module containing the class is imported as though it were a
        module within the context's package (and appropriate subpackages).
        """
        module = self.importAsPackage(transaction, fileName)
        try:
            return getattr(module, className)
        except AttributeError:
            raise AttributeError(
                'Cannot find expected class'
                f' named {className} in {fileName}.') from None

    def loadClass(self, transaction, path):
        className = self.computeClassName(path)
        classFile = join(self._cacheDir, className + ".py")
        mtime = getmtime(path)
        if not exists(classFile) or getmtime(classFile) != mtime:
            context = Context.PSPCLContext(path)
            context.setClassName(className)
            context.setPythonFileName(classFile)
            context.setPythonFileEncoding(self._fileEncoding)
            clc = PSPCompiler.Compiler(context)
            sourceFiles = clc.compile()
            # Set the modification time of the compiled file
            # to be the same as the source file;
            # that's how we'll know if it needs to be recompiled:
            utime(classFile, (getatime(classFile), mtime))
            # Record all included files so we can spot any changes:
            for sourcefile in sourceFiles:
                self._recordFile(sourcefile)
        return self.loadClassFromFile(transaction, classFile, className)
