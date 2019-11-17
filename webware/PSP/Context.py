"""Utility class for keeping track of the context.

A utility class that holds information about the file we are parsing
and the environment we are doing it in.

Copyright (c) by Jay Love, 2000 (mailto:jsliv@jslove.org)

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation or portions thereof, including modifications,
that you make.

This software is based in part on work done by the Jakarta group.
"""

import os


class PSPContext:
    """PSPContext is an abstract base class for Context classes.

    Holds all the common stuff that various parts of the compilation
    will need access to. The items in this class will be used by both
    the compiler and the class generator.
    """

    def getClassPath(self):
        raise NotImplementedError

    def getReader(self):
        raise NotImplementedError

    def getWriter(self):
        raise NotImplementedError

    def getOutputDirectory(self):
        """Provide directory to dump PSP source file to."""
        raise NotImplementedError

    def getServletClassName(self):
        """Return the class name of the servlet being generated."""
        raise NotImplementedError

    def getFullClassName(self):
        """Return the class name including package prefixes.

        Won't use this for now.
        """
        raise NotImplementedError

    def getPythonFileName(self):
        """Return the filename that we are generating to."""
        raise NotImplementedError

    def getPythonFileEncoding(self):
        """Return the encoding of the file that we are generating."""
        raise NotImplementedError

    def setPSPReader(self, reader):
        """Set the PSPReader for this context."""
        raise NotImplementedError

    def setServletWriter(self, writer):
        """Set the PSPWriter instance for this context."""
        raise NotImplementedError

    def setPythonFileName(self, name):
        """Set the name of the .py file to generate."""
        raise NotImplementedError

    def setPythonFileEncoding(self, encoding):
        """Set the encoding of the .py file to generate."""
        raise NotImplementedError


class PSPCLContext(PSPContext):
    """A context for command line compilation.

    Currently used for both command line and PSPServletEngine compilation.
    This class provides all the information necessary during the parsing
    and page generation steps of the PSP compilation process.
    """

    def __init__(self, pspfile):
        PSPContext.__init__(self)
        self._baseUri, self._pspFile = os.path.split(pspfile)
        self._fullPath = pspfile
        self._pyFileEncoding = None

    def getClassPath(self):
        raise NotImplementedError

    def getReader(self):
        """Return the PSPReader object assigned to this context."""
        return self._pspReader

    def getServletWriter(self):
        """Return the ServletWriter object assigned to this context."""
        return self._servletWriter

    def getOutputDirectory(self):
        """Provide directory to dump PSP source file to.

        I am probably doing this in reverse order at the moment.
        I should start with this and get the Python filename from it.
        """
        return os.path.split(self._pyFileName)[0]

    def getServletClassName(self):
        """Return the class name of the servlet being generated."""
        return self._className

    def getFullClassName(self):
        """Return the class name including package prefixes.

        Won't use this for now.
        """
        raise NotImplementedError

    def getPythonFileName(self):
        """Return the filename that we are generating to."""
        return self._pyFileName

    def getPythonFileEncoding(self):
        """Return the encoding of the file that we are generating."""
        return self._pyFileEncoding

    def getPspFileName(self):
        """Return the name of the PSP file from which we are generating."""
        return self._pspFile

    def getFullPspFileName(self):
        """Return the name of the PSP file including its file path."""
        return self._fullPath

    def setPSPReader(self, reader):
        """Set the PSPReader for this context."""
        self._pspReader = reader

    def setServletWriter(self, writer):
        """Set the ServletWriter instance for this context."""
        self._servletWriter = writer

    def setPythonFileName(self, name):
        """Set the name of the .py file to generate."""
        self._pyFileName = name

    def setPythonFileEncoding(self, encoding):
        """Set the encoding of the .py file to generate."""
        self._pyFileEncoding = encoding

    def setClassName(self, name):
        """Set the class name to create."""
        self._className = name

    def resolveRelativeURI(self, uri):
        """This is used mainly for including files.

        It simply returns the location relative to the base context
        directory, ie Examples/. If the filename has a leading /,
        it is assumed to be an absolute path.
        """
        if os.path.isabs(uri):
            return uri
        return os.path.join(self._baseUri, uri)

    def getBaseUri(self):
        """Return the base URI for the servlet."""
        return self._baseUri
