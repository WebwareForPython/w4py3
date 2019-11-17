"""Generate Python code from PSP templates.

This module holds the classes that generate the Python code resulting
from the PSP template file. As the parser encounters PSP elements,
it creates a new Generator object for that type of element.
Each of these elements is put into a list maintained by the
ParseEventHandler object. When it comes time to output the source code,
each generator is called in turn to create its source.

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

from . import BraceConverter, PSPUtils

# This is global so that the ParseEventHandler and this module agree:
ResponseObject = 'res'


class GenericGenerator:
    """Base class for all the generators"""

    def __init__(self, ctxt=None):
        self._ctxt = ctxt
        self.phase = 'Service'


# pylint: disable=unused-argument

class ExpressionGenerator(GenericGenerator):
    """This class handles expression blocks.

    It simply outputs the (hopefully) python expression within the block
    wrapped with a _formatter() call.
    """

    def __init__(self, chars):
        self.chars = chars
        GenericGenerator.__init__(self)

    def generate(self, writer, phase=None):
        writer.println(
            f'res.write(_formatter({PSPUtils.removeQuotes(self.chars)}))')


class CharDataGenerator(GenericGenerator):
    """This class handles standard character output, mostly HTML.

    It just dumps it out. Need to handle all the escaping of characters.
    It's just skipped for now.
    """

    def __init__(self, chars):
        GenericGenerator.__init__(self)
        self.chars = chars

    def generate(self, writer, phase=None):
        # Quote any existing backslash so generated Python will not
        # interpret it when running.
        self.chars = self.chars.replace('\\', r'\\')
        # Quote any single quotes so it does not get confused with
        # our triple-quotes:
        self.chars = self.chars.replace('"', r'\"')
        self.generateChunk(writer)

    def generateChunk(self, writer, start=0, stop=None):
        writer.printIndent()  # gives one level of indentation
        writer.printChars(ResponseObject + '.write("""')
        writer.printChars(self.chars)
        writer.printChars('""")')
        writer.printChars('\n')

    def mergeData(self, cdGen):
        self.chars += cdGen.chars


class ScriptGenerator(GenericGenerator):
    """Generate scripts."""

    def __init__(self, chars, attrs):
        GenericGenerator.__init__(self)
        self.chars = chars

    def generate(self, writer, phase=None):
        self.chars = PSPUtils.normalizeIndentation(self.chars)
        if writer._useBraces:
            # Send lines to be output by the braces generator:
            braceConverter = BraceConverter.BraceConverter()
            lines = PSPUtils.splitLines(PSPUtils.removeQuotes(self.chars))
            for line in lines:
                braceConverter.parseLine(line, writer)
            return
        # Check for whitespace at beginning and if less than 2 spaces, remove:
        if self.chars.startswith(' ') and not self.chars.startswith('  '):
            self.chars = self.chars.lstrip()
        lines = PSPUtils.splitLines(PSPUtils.removeQuotes(self.chars))
        if not lines:
            return  # ignore any empty tag
        # userIndent check
        if lines[-1].endswith('$'):
            lastLine = lines[-1] = lines[-1][:-1]
            if not lastLine:
                lastLine = lines[-2]  # handle endscript marker on its own line
            count = 0
            while lastLine[count].isspace():
                count += 1
            userIndent = lastLine[:count]
        else:
            userIndent = writer._emptyString
            lastLine = lines[-1]
        # Print out code (moved from above):
        writer._userIndent = writer._emptyString  # reset to none
        writer.printList(lines)
        writer.printChars('\n')
        # Check for a block:
        # (Known issue: this fails if '#' part of string)
        commentStart = lastLine.find('#')
        if commentStart >= 0:
            lastLine = lastLine[:commentStart]
        blockCheck = lastLine.rstrip()
        if blockCheck.endswith(':'):
            writer.pushIndent()
            writer.println()
            writer._blockCount += 1
            # Check for end of block, "pass" by itself:
        if self.chars.strip() == 'pass' and writer._blockCount > 0:
            writer.popIndent()
            writer.println()
            writer._blockCount -= 1
        # Set userIndent for subsequent HTML:
        writer._userIndent = userIndent


class EndBlockGenerator(GenericGenerator):

    def __init__(self):
        GenericGenerator.__init__(self)

    def generate(self, writer, phase=None):
        if writer._blockCount > 0:
            writer.popIndent()
            writer.println()
            writer._blockCount -= 1
        writer._userIndent = writer._emptyString


class ScriptFileGenerator(GenericGenerator):
    """Add Python code at the file/module level."""

    def __init__(self, chars, attrs):
        GenericGenerator.__init__(self)
        self.phase = 'psp:file'
        self.attrs = attrs
        self.chars = chars

    def generate(self, writer, phase=None):
        writer.println('\n# File level user code')
        pySrc = PSPUtils.normalizeIndentation(self.chars)
        pySrc = PSPUtils.splitLines(PSPUtils.removeQuotes(pySrc))
        writer.printList(pySrc)


class ScriptClassGenerator(GenericGenerator):
    """Add Python code at the class level."""

    def __init__(self, chars, attrs):
        GenericGenerator.__init__(self)
        self.phase = 'psp:class'
        self.attrs = attrs
        self.chars = chars

    def generate(self, writer, phase=None):
        writer.println('# Class level user code\n')
        pySrc = PSPUtils.normalizeIndentation(self.chars)
        pySrc = PSPUtils.splitLines(PSPUtils.removeQuotes(pySrc))
        writer.printList(pySrc)


class MethodGenerator(GenericGenerator):
    """Generate class methods defined in the PSP page.

    There are two parts to method generation.
    This class handles getting the method name and parameters set up.
    """

    def __init__(self, chars, attrs):
        GenericGenerator.__init__(self)
        self.phase = 'Declarations'
        self.attrs = attrs

    def generate(self, writer, phase=None):
        writer.printIndent()
        writer.printChars('def ')
        writer.printChars(self.attrs['name'])
        writer.printChars('(')
        writer.printChars('self')
        if 'params' in self.attrs and self.attrs['params']:
            writer.printChars(', ')
            writer.printChars(self.attrs['params'])
        writer.printChars('):\n')
        if self.attrs['name'] == 'awake':
            writer._awakeCreated = True
            writer.pushIndent()
            writer.println('self.initPSP()\n')
            writer.popIndent()
            writer.println()


class MethodEndGenerator(GenericGenerator):
    """Part of class method generation.

    After MethodGenerator, MethodEndGenerator actually generates
    the code for the method body.
    """

    def __init__(self, chars, attrs):
        GenericGenerator.__init__(self)
        self.phase = 'Declarations'
        self.attrs = attrs
        self.chars = chars

    def generate(self, writer, phase=None):
        writer.pushIndent()
        writer.printList(PSPUtils.splitLines(
            PSPUtils.removeQuotes(self.chars)))
        writer.printChars('\n')
        writer.popIndent()


class IncludeGenerator(GenericGenerator):
    """Handle psp:include directives.

    This is a new version of this directive that actually
    forwards the request to the specified page.
    """

    _theFunction = (
        '__pspincludepath = "{}"\n'
        'self.transaction().application().includeURL('
        'self.transaction(), __pspincludepath)')

    def __init__(self, attrs, param, ctxt):
        GenericGenerator.__init__(self, ctxt)
        self.attrs = attrs
        self.param = param
        self.scriptGenerator = None

        self.url = attrs.get('path')
        if self.url is None:
            raise AttributeError('No path attribute in include')

        self.scriptGenerator = ScriptGenerator(
            self._theFunction.format(self.url), None)

    def generate(self, writer, phase=None):
        """Just insert theFunction."""
        self.scriptGenerator.generate(writer, phase)


class InsertGenerator(GenericGenerator):
    """Include files designated by the psp:insert syntax.

    If the attribute 'static' is set to True or 1, we include the file now,
    at compile time. Otherwise, we use a function added to every PSP page
    named ``__includeFile``, which reads the file at run time.
    """

    def __init__(self, attrs, param, ctxt):
        GenericGenerator.__init__(self, ctxt)
        self.attrs = attrs
        self.param = param
        self.scriptGenerator = None

        self.page = attrs.get('file')
        if not self.page:
            raise AttributeError('No file attribute in include')
        path = self._ctxt.resolveRelativeURI(self.page)
        if not os.path.exists(path):
            print(self.page)
            raise IOError(f'Invalid included file {path!r}')
        self.page = path

        self.static = str(attrs.get('static')).lower() in ('true', 'yes', '1')
        if not self.static:
            path = path.replace('\\', '\\\\')
            self.scriptGenerator = ScriptGenerator(
                f"self.__includeFile({path!r})", None)

    def generate(self, writer, phase=None):
        # JSP does this in the servlet. I'm doing it here because
        # I have triple quotes. Note: res.write statements inflate
        # the size of the resulting class file when it is cached.
        # Cut down on those by using a single res.write on the whole
        # file, after escaping any triple-double quotes.
        if self.static:
            with open(self.page) as f:
                data = f.read()
            data = data.replace('"""', r'\"""')
            writer.println(f'res.write("""{data}""")')
            writer.println()
        else:
            self.scriptGenerator.generate(writer, phase)
