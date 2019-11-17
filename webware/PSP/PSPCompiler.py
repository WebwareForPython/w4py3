"""A simple little module that organizes the actual page generation.

Copyright (c) by Jay Love, 2000 (mailto:jsliv@jslove.org)

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation or portions thereof, including modifications,
that you make.

This software is based in part on work done by the Jakarta group.
"""

from .StreamReader import StreamReader
from .ServletWriter import ServletWriter
from .PSPParser import PSPParser
from .ParseEventHandler import ParseEventHandler


class Compiler:
    """The main compilation class."""

    def __init__(self, context):
        self._ctxt = context

    def compile(self):
        """Compile the PSP context and return a set of all source files."""
        reader = StreamReader(self._ctxt.getPspFileName(), self._ctxt)
        reader.init()
        writer = ServletWriter(self._ctxt)
        self._ctxt.setPSPReader(reader)
        self._ctxt.setServletWriter(writer)
        parser = PSPParser(self._ctxt)
        handler = ParseEventHandler(self._ctxt, parser)
        parser.setEventHandler(handler)
        handler.beginProcessing()
        parser.parse()
        sourceFiles = set(reader.sourceFiles)
        handler.endProcessing()
        writer.close()
        return sourceFiles
