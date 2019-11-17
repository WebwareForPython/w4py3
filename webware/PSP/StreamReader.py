"""This module co-ordinates the reading of the source file.

It maintains the current position of the parser in the source file.

Copyright (c) by Jay Love, 2000 (mailto:jsliv@jslove.org)

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation or portions thereof, including modifications,
that you make.

This software is based in part on work done by the Jakarta group.
"""

from copy import copy
import os

from .PSPUtils import PSPParserException


class Mark:
    """This class marks a point in an input stream."""

    def __init__(
            self, reader,
            fileId=None, stream=None, inBaseDir=None, encoding=None):
        if not isinstance(reader, StreamReader):
            raise TypeError('First argument must be a StreamReader')
        self.reader = reader
        self.fileId = fileId
        self.includeStack = []
        self.cursor = 0
        self.stream = stream
        self.baseDir = inBaseDir
        self.encoding = encoding

    def __str__(self):
        return f'{self.getFile()}({self.cursor})'

    def getFile(self):
        return self.reader.getFile(self.fileId)

    def pushStream(self, inFileId, inStream, inBaseDir, inEncoding):
        self.includeStack.append(
            (self.cursor, self.fileId, self.baseDir,
             self.encoding, self.stream))
        self.cursor = 0
        self.fileId = inFileId
        self.stream = inStream
        self.baseDir = inBaseDir
        self.encoding = inEncoding

    def popStream(self):
        if not self.includeStack:
            return False
        (self.cursor, self.fileId, self.baseDir,
         self.encoding, self.stream) = self.includeStack.pop()
        return True


class StreamReader:
    """This class handles the PSP source file.

    It provides the characters to the other parts of the system.
    It can move forward and backwards in a file and remember locations.
    """

    def __init__(self, filename, ctxt):
        self._pspFile = filename
        self._ctxt = ctxt
        self.sourceFiles = []
        self.current = None
        self.master = None

    def init(self):
        self.pushFile(self._ctxt.getFullPspFileName())

    def registerSourceFile(self, filepath):
        self.sourceFiles.append(filepath)
        return len(self.sourceFiles) - 1

    def pushFile(self, filepath, encoding=None):
        if self.master is None:
            parent = None
            self.master = filepath
        else:
            parent = os.path.split(self.master)[0]
        isAbsolute = os.path.isabs(filepath)
        if parent is not None and not isAbsolute:
            filepath = os.path.join(parent, filepath)
        fileId = self.registerSourceFile(filepath)
        with open(filepath, 'r') as handle:
            stream = handle.read()
            handle.seek(0, 0)
            if self.current is None:
                self.current = Mark(
                    self, fileId, stream, self._ctxt.getBaseUri(), encoding)
            else:
                self.current.pushStream(  # don't use yet
                    fileId, stream, self._ctxt.getBaseUri(), encoding)

    def popFile(self):
        if self.current is None:
            return None
        return self.current.popStream()

    def getFile(self, i):
        return self.sourceFiles[i]

    def newSourceFile(self, filename):
        if filename in self.sourceFiles:
            return None
        self.sourceFiles.append(filename)
        return len(self.sourceFiles)

    def mark(self):
        return copy(self.current)

    def skipUntil(self, s):
        """Greedy search.

        Return the point before the string, but move reader past it.
        """
        newCursor = self.current.stream.find(s, self.current.cursor)
        if newCursor < 0:
            self.current.cursor = len(self.current.stream)
            if self.hasMoreInput():
                self.popFile()
                self.skipUntil(s)
            else:
                raise EOFError
        else:
            self.current.cursor = newCursor
            mark = self.mark()
            self.current.cursor += len(s)
            return mark

    def reset(self, mark):
        self.current = mark

    def matches(self, s):
        if s == self.current.stream[
                self.current.cursor:self.current.cursor + len(s)]:
            return True
        return False

    def advance(self, length):
        """Advance length characters"""
        if length + self.current.cursor <= len(self.current.stream):
            self.current.cursor += length
        else:
            offset = len(self.current.stream) - self.current.cursor
            self.current.cursor = len(self.current.stream)
            if self.hasMoreInput():
                self.advance(length - offset)
            else:
                raise EOFError()

    def nextChar(self):
        if not self.hasMoreInput():
            return -1
        char = self.current.stream[self.current.cursor]
        self.advance(1)
        return char

    def isSpace(self):
        """No advancing."""
        return self.current.stream[self.current.cursor] in (' ', '\n')

    def isDelimiter(self):
        if not self.isSpace():
            c = self.peekChar()
            # Look for single character work delimiter:
            if c in ('=', '"', "'", '/'):
                return True
            # Look for end of comment or basic end tag:
            if c == '-':
                mark = self.mark()
                c = self.nextChar()
                try:
                    return c == '>' or (c == '-' and self.nextChar() == '>')
                finally:
                    self.reset(mark)
        else:
            return True

    def peekChar(self, cnt=1):
        if self.hasMoreInput():
            return self.current.stream[
                self.current.cursor:self.current.cursor+cnt]
        raise EOFError

    def skipSpaces(self):
        i = 0
        while self.isSpace():
            self.nextChar()
            i += 1
        return i

    def getChars(self, start, stop):
        mark = self.mark()
        self.reset(start)
        chars = self.current.stream[start.cursor:stop.cursor]
        self.reset(mark)
        return chars

    def hasMoreInput(self):
        if self.current.cursor >= len(self.current.stream):
            while self.popFile():
                if self.current.cursor < len(self.current.stream):
                    return True
            return False
        return True

    def nextContent(self):
        """Find next < char."""
        currentCursor = self.current.cursor
        self.current.cursor += 1
        newCursor = self.current.stream.find('<', self.current.cursor)
        if newCursor < 0:
            newCursor = len(self.current.stream)
        self.current.cursor = newCursor
        return self.current.stream[currentCursor:newCursor]

    def parseTagAttributes(self):
        """Parse the attributes at the beginning of a tag."""
        values = {}
        while True:
            self.skipSpaces()
            c = self.peekChar()
            if c == '>':
                return values
            if c == '-':
                mark = self.mark()
                self.nextChar()
                try:
                    if self.nextChar() == '-' and self.nextChar() == '>':
                        return values
                finally:
                    self.reset(mark)
            elif c == '%':
                mark = self.mark()
                self.nextChar()
                try:
                    if self.peekChar() == '>':
                        return values
                finally:
                    self.reset(mark)
            elif not c:
                break
            self.parseAttributeValue(values)
        raise PSPParserException('Unterminated attribute')

    def parseAttributeValue(self, valueDict):
        self.skipSpaces()
        name = self.parseToken(0)
        self.skipSpaces()
        if self.peekChar() != '=':
            raise PSPParserException('No attribute value')
        self.nextChar()
        self.skipSpaces()
        value = self.parseToken(1)
        self.skipSpaces()
        valueDict[name] = value

    def parseToken(self, quoted):
        # This may not be quite right:
        buffer = []
        self.skipSpaces()
        c = self.peekChar()
        if quoted:
            if c in ('"', "'"):
                endQuote = c
                self.nextChar()
                c = self.peekChar()
                while c is not None and c != endQuote:
                    c = self.nextChar()
                    if c == '\\':
                        c = self.nextChar()
                    buffer.append(c)
                    c = self.peekChar()
                if c is None:
                    raise PSPParserException('Unterminated attribute value')
                self.nextChar()
        else:
            if not self.isDelimiter():
                while not self.isDelimiter():
                    c = self.nextChar()
                    if c == '\\':
                        c = self.peekChar()
                        if c in ('"', "'", '>', '%'):
                            c = self.nextChar()
                    buffer.append(c)
        return ''.join(buffer)
