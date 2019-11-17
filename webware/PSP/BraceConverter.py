"""BraceConverter.py

Contributed 2000-09-04 by Dave Wallace (dwallace@delanet.com)

Converts Brace-blocked Python into normal indented Python.
Brace-blocked Python is non-indentation aware and blocks are
delimited by ':{' and '}' pairs.

Thus::

    for x in range(10) :{
        if x % 2 :{ print(x) } else :{ print(z) }
    }

Becomes (roughly, barring some spurious whitespace)::

    for x in range(10):
        if x % 2:
            print(x)
        else:
            print(z)

This implementation is fed a line at a time via parseLine(),
outputs to a PSPServletWriter, and tracks the current quotation
and block levels internally.
"""

import re


class BraceConverter:

    _reCharSkip = re.compile("(^[^\"'{}:#]+)")
    _reColonBrace = re.compile(r":\s*{\s*([^\s].*)?$")

    def __init__(self):
        self.inQuote = False
        self.dictLevel = 0

    def parseLine(self, line, writer):
        """Parse a line.

        The only public method of this class, call with subsequent lines
        and an instance of PSPServletWriter.
        """
        self.line = line
        if self.inQuote and self.line:
            self.skipQuote(writer)
        self.line = self.line.lstrip()
        if not self.line:
            writer.printChars('\n')
            return
        writer.printIndent()
        while self.line:
            while self.inQuote and self.line:
                self.skipQuote(writer)
            match = self._reCharSkip.search(self.line)
            if match:
                writer.printChars(self.line[:match.end(1)])
                self.line = self.line[match.end(1):]
            else:
                c = self.line[0]
                if c == "'":
                    self.handleQuote("'", writer)
                    self.skipQuote(writer)
                elif c == '"':
                    self.handleQuote('"', writer)
                    self.skipQuote(writer)
                elif c == '{':
                    self.openBrace(writer)
                elif c == '}':
                    self.closeBrace(writer)
                elif c == ':':
                    self.openBlock(writer)
                elif c == '#':
                    writer.printChars(self.line)
                    self.line = ''
                else:
                    # should never get here
                    raise Exception()
        writer.printChars('\n')

    def openBlock(self, writer):
        """Open a new block."""
        match = self._reColonBrace.match(self.line)
        if match and not self.dictLevel:
            writer.printChars(':')
            writer.pushIndent()
            if match.group(1):
                # text follows :{, if it's a comment, leave it on same line,
                # else start a new line and leave the text for processing
                if match.group(1)[0] == '#':
                    writer.printChars(' ' + match.group(1))
                    self.line = ''
                else:
                    writer.printChars('\n')
                    writer.printIndent()
                    self.line = match.group(1)
            else:
                self.line = ''
        else:
            writer.printChars(':')
            self.line = self.line[1:]

    def openBrace(self, writer):
        """Open brace encountered."""
        writer.printChars('{')
        self.line = self.line[1:]
        self.dictLevel += 1

    def closeBrace(self, writer):
        """Close brace encountered."""
        if self.dictLevel:
            writer.printChars('}')
            self.line = self.line[1:]
            self.dictLevel -= 1
        else:
            writer.popIndent()
            self.line = self.line[1:].lstrip()
            if self.line:
                writer.printChars('\n')
                writer.printIndent()

    def skipQuote(self, writer):
        """Skip to end of quote.

        Skip over all chars until the line is exhausted
        or the current non-escaped quote sequence is encountered.
        """
        pos = self.line.find(self.quoteChars)
        if pos < 0:
            writer.printChars(self.line)
            self.line = ''
        elif pos > 0 and self.line[pos - 1] == '\\':
            pos += 1
            writer.printChars(self.line[:pos])
            self.line = self.line[pos:]
            self.skipQuote(writer)
        else:
            pos += len(self.quoteChars)
            writer.printChars(self.line[:pos])
            self.line = self.line[pos:]
            self.inQuote = False

    def handleQuote(self, quote, writer):
        """Check and handle if current pos is a single or triple quote."""
        self.inQuote = True
        triple = quote * 3
        if self.line[0:3] == triple:
            self.quoteChars = triple
            writer.printChars(triple)
            self.line = self.line[3:]
        else:
            self.quoteChars = quote
            writer.printChars(quote)
            self.line = self.line[1:]
