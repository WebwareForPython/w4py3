"""This module holds the actual file writer class.

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

from io import StringIO


class ServletWriter:
    """This file creates the servlet source code.

    Well, it writes it out to a file at least.
    """

    _tab = '\t'
    _spaces = '    '  # 4 spaces
    _emptyString = ''

    def __init__(self, ctxt):
        self._pyFilename = ctxt.getPythonFileName()
        self._file = StringIO()
        self._tabCount = 0
        self._blockCount = 0  # a hack to handle nested blocks of python code
        self._indentSpaces = self._spaces
        self._useTabs = False
        self._useBraces = False
        self._indent = '    '
        self._userIndent = self._emptyString
        self._awakeCreated = False  # means that awake() needs to be generated

    def setIndentSpaces(self, amt):
        self._indentSpaces = ' ' * amt
        self.setIndention()

    def setIndention(self):
        self._indent = '\t' if self._useTabs else self._indentSpaces

    def setIndentType(self, indentType):
        if indentType == 'tabs':
            self._useTabs = True
            self.setIndention()
        elif indentType == 'spaces':
            self._useTabs = False
            self.setIndention()
        elif indentType == 'braces':
            self._useTabs = False
            self._useBraces = True
            self.setIndention()

    def close(self):
        pyCode = self._file.getvalue()
        self._file.close()
        if os.path.exists(self._pyFilename):
            os.remove(self._pyFilename)
        with open(self._pyFilename, 'w') as f:
            f.write(pyCode)

    def pushIndent(self):
        """this is very key, have to think more about it"""
        self._tabCount += 1

    def popIndent(self):
        if self._tabCount > 0:
            self._tabCount -= 1

    def printComment(self, start, stop, chars):
        if start and stop:
            self.println(f'## from {start}')
            self.println(f'## from {stop}')
        if chars:
            lines = chars.splitlines()
            for line in lines:
                self._file.write(self.indent(''))
                self._file.write('##')
                self._file.write(line)

    def quoteString(self, s):
        """Escape the string."""
        if s is None:
            return 'None'  # this probably won't work
        return 'r' + s

    def indent(self, s):
        """Indent the string."""
        if self._userIndent or self._tabCount > 0:
            return self._userIndent + self._indent * self._tabCount + s
        return s

    def println(self, line=None):
        """Print with indentation and a newline if none supplied."""
        if line:
            self._file.write(self.indent(line))
            if not line.endswith('\n'):
                self._file.write('\n')
        else:
            self._file.write(self.indent('\n'))

    def printChars(self, s):
        """Just prints what its given."""
        self._file.write(s)

    def printMultiLn(self, s):
        raise NotImplementedError

    def printList(self, strList):
        """Prints a list of strings with indentation and a newline."""
        for line in strList:
            self.printChars(self.indent(line))
            self.printChars('\n')

    def printIndent(self):
        """Just prints tabs."""
        self.printChars(self.indent(''))
