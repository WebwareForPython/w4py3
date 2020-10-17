"""The PSP parser.

This module handles the actual reading of the characters in the source
PSP file and checking it for valid psp tokens. When it finds one,
it calls ParseEventHandler with the characters it found.

Copyright (c) by Jay Love, 2000 (mailto:jsliv@jslove.org)

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation or portions thereof, including modifications,
that you make.

This software is based in part on work done by the Jakarta group.
"""

from io import StringIO

from .PSPUtils import checkAttributes, PSPParserException


checklist = []


def checker(method):
    """Decorator for adding a method to the checklist."""
    checklist.append(method)
    return method


class PSPParser:
    """The main PSP parser class.

    The PSPParser class does the actual sniffing through the input file
    looking for anything we're interested in. Basically, it starts by
    looking at the code looking for a '<' symbol. It looks at the code by
    working with a PSPReader object, which handles the current location in
    the code. When it finds one, it calls a list of checker methods,
    asking each if it recognizes the characters as its kind of input.
    When the checker methods look at the characters, if they want it,
    they go ahead and gobble it up and set up to create it in the servlet
    when the time comes. When they return, they return true if they accept
    the character, and the PSPReader object cursor is positioned past the
    end of the block that the checker method accepted.
    """

    checklist = checklist  # global list of checker methods

    def __init__(self, ctxt):
        self._reader = ctxt.getReader()
        self._writer = ctxt.getServletWriter()
        self._handler = None
        self.cout = StringIO()  # for dumping HTML that none of the check wants
        self.tmplStart = None  # marks the start of HTML code
        self.tmplStop = None  # marks the end of HTML code
        self.currentFile = self._reader.mark().getFile()

    def setEventHandler(self, handler):
        """Set the handler this parser will use when it finds PSP code."""
        self._handler = handler

    def flushCharData(self, start, stop):
        """Dump everything to the char data handler.

        Dump all the HTML that we've accumulated over to the character data
        handler in the event handler object.
        """
        data = self.cout.getvalue()
        self.cout.close()
        if data:  # make sure there's something there
            self._handler.handleCharData(start, stop, data)
        self.cout = StringIO()

    @checker
    def commentCheck(self, _handler, reader):
        """Comments just get eaten."""
        if reader.matches('<%--'):
            reader.advance(4)
            if reader.skipUntil('--%>') is None:
                raise PSPParserException('Comment not terminated')
            self.flushCharData(self.tmplStart, self.tmplStop)
            return True
        return False

    @checker
    def checkExpression(self, handler, reader):
        """Look for "expressions" and handle them."""
        if not reader.matches('<%='):
            return False
        reader.advance(3)  # eat the opening tag
        reader.peekChar()
        reader.skipSpaces()
        start = reader.mark()
        stop = reader.skipUntil('%>')
        if stop is None:
            raise PSPParserException('Expression not terminated')
        handler.setTemplateInfo(self.tmplStart, self.tmplStop)
        handler.handleExpression(start, stop, None)
        return True

    @checker
    def checkDirective(self, handler, reader):
        """Check for directives; for now we support only page and include."""
        if not reader.matches('<%@'):
            return False
        start = reader.mark()
        reader.advance(3)
        reader.skipSpaces()
        for directive in ('page', 'include', 'taglib'):
            if reader.matches(directive):
                match = directive
                break
        else:
            raise PSPParserException('Invalid directive')
        reader.advance(len(match))
        # parse the directive attr:val pair dictionary
        attrs = reader.parseTagAttributes()
        if match == 'page':
            checkAttributes('Page directive', attrs, ([], {
                'imports', 'extends', 'method',
                'isThreadSafe', 'isInstanceSafe',
                'indentType', 'indentSpaces',
                'gobbleWhitespace', 'formatter'}))
        elif match == 'include':
            checkAttributes('Include directive', attrs, (['file'], []))
        else:
            raise PSPParserException(f'{match} directive not implemented')
        reader.skipSpaces()  # skip to where we expect a close tag
        if reader.matches('%>'):
            reader.advance(2)  # advance past it
        else:
            raise PSPParserException('Directive not terminated')
        stop = reader.mark()
        handler.setTemplateInfo(self.tmplStart, self.tmplStop)
        handler.handleDirective(match, start, stop, attrs)
        return True

    @checker
    def checkEndBlock(self, handler, reader):
        """Check for the end of a block."""
        start = reader.mark()
        if reader.matches('<%'):
            reader.advance(2)
            reader.skipSpaces()
            if reader.matches('end'):
                reader.advance(3)
                reader.skipSpaces()
                if reader.matches('%>'):
                    reader.advance(2)
                    handler.setTemplateInfo(self.tmplStart, self.tmplStop)
                    handler.handleEndBlock()
                    return True
                if reader.matches('$%>'):
                    reader.advance(3)
                    handler.setTemplateInfo(self.tmplStart, self.tmplStop)
                    handler.handleEndBlock()
                    print('INFO: A $ at the end of an end tag does nothing.')
                    return True
        # that wasn't it
        reader.reset(start)
        return False

    @checker
    def checkScript(self, handler, reader):
        """The main thing we're after. Check for embedded scripts."""
        if not reader.matches('<%'):
            return False
        reader.advance(2)
        # don't skip as spaces may be significant; leave this for the generator
        start = reader.mark()
        try:
            stop = reader.skipUntil('%>')
        except EOFError as e:
            raise EOFError(
                "Reached EOF while looking for ending script tag") from e
        if stop is None:
            raise PSPParserException('Script not terminated')
        handler.setTemplateInfo(self.tmplStart, self.tmplStop)
        handler.handleScript(start, stop, None)
        return True

    @checker
    def checkScriptFile(self, handler, reader):
        """Check for file level code.

        Check for Python code that must go to the top of the generated module::

            <psp:file>
                import xyz
                print('hi Mome!')
                def foo(): return 'foo'
            </psp:file>
        """
        if not reader.matches('<psp:file>'):
            return False
        reader.advance(10)
        start = reader.mark()
        try:
            stop = reader.skipUntil('</psp:file>')
            if stop is None:
                raise PSPParserException(
                    'Script not terminated in <psp:file> block')
        except EOFError as e:
            raise EOFError(
                'Reached EOF while looking for'
                ' ending script tag </psp:file>') from e
        handler.setTemplateInfo(self.tmplStart, self.tmplStop)
        handler.handleScriptFile(start, stop, None)
        return True

    @checker
    def checkScriptClass(self, handler, reader):
        """Check for class level code.

        Check for Python code that should go in the class definition::

            <psp:class>
                def foo(self):
                    return self.dosomething()
            </psp:class>
        """
        if not reader.matches('<psp:class>'):
            return False
        reader.advance(11)
        start = reader.mark()
        try:
            stop = reader.skipUntil('</psp:class>')
            if stop is None:
                raise PSPParserException(
                    'Script not terminated in <psp:class> block')
        except EOFError as e:
            raise EOFError(
                'Reached EOF while looking for'
                ' ending script tag </psp:class>') from e
        handler.setTemplateInfo(self.tmplStart, self.tmplStop)
        handler.handleScriptClass(start, stop, None)
        return True

    @checker
    def checkMethod(self, handler, reader):
        """Check for class methods defined in the page.

        We only support one format for these,
        ``<psp:method name="xxx" params="xxx,xxx">``
        Then the function body, then </psp:method>.
        """
        if not reader.matches('<psp:method'):
            return False
        start = reader.mark()
        reader.advance(11)
        attrs = reader.parseTagAttributes()
        checkAttributes('method', attrs, (['name'], ['params']))
        reader.skipSpaces()
        if not reader.matches('>'):
            raise PSPParserException('Expected method declaration close')
        reader.advance(1)
        stop = reader.mark()
        handler.setTemplateInfo(self.tmplStart, self.tmplStop)
        handler.handleMethod(start, stop, attrs)
        start = stop
        # skip past the close marker, return the point before the close marker
        stop = reader.skipUntil('</psp:method>')
        handler.handleMethodEnd(start, stop, attrs)
        return True

    @checker
    def checkInclude(self, handler, reader):
        """Check for inserting another pages output in this spot."""
        if not reader.matches('<psp:include'):
            return False
        reader.advance(12)
        reader.skipSpaces()
        attrs = reader.parseTagAttributes()
        checkAttributes('include', attrs, (['path'], []))
        reader.skipSpaces()
        if not reader.matches('>'):
            raise PSPParserException('Include bodies not implemented')
        reader.advance(1)
        handler.setTemplateInfo(self.tmplStart, self.tmplStop)
        handler.handleInclude(attrs, None)
        return True

    @checker
    def checkInsert(self, handler, reader):
        """Check for straight character dumps.

        No big hurry for this. It's almost the same as the page include
        directive.  This is only a partial implementation of what JSP does.
        JSP can pull it from another server, servlet, JSP page, etc.
        """
        if not reader.matches('<psp:insert'):
            return False
        reader.advance(11)
        reader.skipSpaces()
        attrs = reader.parseTagAttributes()
        checkAttributes('insert', attrs, (['file'], []))
        reader.skipSpaces()
        if not reader.matches('>'):
            raise PSPParserException('Insert bodies not implemented')
        reader.advance(1)
        handler.setTemplateInfo(self.tmplStart, self.tmplStop)
        handler.handleInsert(attrs, None)
        return True

    def parse(self, until=None):
        """Parse the PSP file."""
        reader = self._reader
        handler = self._handler
        noPspElement = False
        while reader.hasMoreInput():
            # This is for XML style blocks, which we're not handling yet:
            if until and reader.matches(until):
                return
            # If the file the reader is working on has changed due to
            # a push or pop, flush any char data from the old file:
            if reader.mark().getFile() != self.currentFile:
                self.flushCharData(self.tmplStart, self.tmplStop)
                self.currentFile = reader.mark().getFile()
                self.tmplStart = reader.mark()
            for checkFunc in self.checklist:
                if checkFunc(self, handler, reader):
                    noPspElement = False
                    break
            else:
                if not noPspElement:
                    self.tmplStart = reader.mark()
                    noPspElement = True
                s = reader.nextContent()  # skip till the next possible tag
                self.tmplStop = reader.mark()  # mark the end of HTML data
                self.cout.write(s)  # write out the raw HTML data
            self.flushCharData(self.tmplStart, self.tmplStop)  # dump the rest
