"""HTMLTag.py

HTMLTag defines a class of the same name that represents HTML content.
An additional HTMLReader class kicks off the process of reading an HTML
file into a set of tags::

    from WebUtils.HTMLTag import HTMLReader
    reader = HTMLReader()
    tag = reader.readFileNamed('foo.html')
    tag.pprint()

Tags have attributes and children, which makes them hierarchical.
See HTMLTag class docs for more info.

Note that you imported HTMLReader instead of HTMLTag.
You only need the latter if you plan on creating tags directly.

You can discard the reader immediately if you like::

    tag = HTMLReader().readFileNamed('foo.html')

The point of reading HTML into tag objects is so that you have a concrete,
Pythonic data structure to work with. The original motivation for such a
beast was in building automated regression test suites that wanted granular,
structured access to the HTML output by the web application.

See the doc string for HTMLTag for examples of what you can do with tags.
"""

import sys

from html.parser import HTMLParser

from MiscUtils import NoDefault, AbstractError


class HTMLTagError(Exception):
    """General HTML tag error"""

    def __init__(self, msg, **values):
        Exception.__init__(self, msg)
        self.values = values.copy()


class HTMLTagAttrLookupError(HTMLTagError, LookupError):
    """HTML tag attribute lookup error"""


class HTMLTagUnbalancedError(HTMLTagError):
    """Unbalanced HTML tag error"""


class HTMLNotAllowedError(HTMLTagError):
    """HTML tag not allowed here error"""


class HTMLTagProcessingInstructionError(HTMLTagError):
    """HTML tag processing instruction error"""


class HTMLTagIncompleteError(HTMLTagError):
    """HTML tag incomplete error"""


DefaultEmptyTags = (
    'area basefont base bgsound br col colgroup frame hr'
    ' img input isindex link meta spacer wbr').split()


class HTMLTag:
    """Container class for representing HTML as tag objects.

    Tags essentially have 4 major attributes:

      * name
      * attributes
      * children
      * subtags

    Name is simple:
        print(tag.name())

    Attributes are dictionary-like in nature::

        print(tag.attr('color'))  # throws an exception if no color
        print(tag.attr('bgcolor', None))  # returns None if no bgcolor
        print(tag.attrs())

    Children are all the leaf parts of a tag, consisting of other tags
    and strings of character data::

        print(tag.numChildren())
        print(tag.childAt(0))
        print(tag.children())

    Subtags is a convenient list of only the tags in the children::

        print(tag.numSubtags())
        print(tag.subtagAt(0))
        print(tag.subtags())

    You can search a tag and all the tags it contains for a tag with
    a particular attribute matching a particular value::

        print(tag.tagWithMatchingAttr('width', '100%'))

    An HTMLTagAttrLookupError is raised if no matching tag is found.
    You can avoid this by providing a default value::

        print(tag.tagWithMatchingAttr('width', '100%', None))

    Looking for specific 'id' attributes is common in regression testing
    (it allows you to zero in on logical portions of a page),
    so a convenience method is provided::

        tag = htmlTag.tagWithId('accountTable')
    """

    # region Init and reading

    def __init__(self, name, lineNumber=None):
        if '\n' in name:
            raise ValueError('Tag name must not contain new lines')
        self._name = name
        self._attrs = {}
        self._children = []
        self._subtags = []
        self._lineNumber = lineNumber
        # Used by closedBy() and __repr__, helps with HTMLReader error messages
        self._isClosed = False

    def readAttr(self, name, value):
        """Set an attribute of the tag with the given name and value.

        A HTMLTagAttrLookupError is raised if an attribute is set twice.
        """
        attrs = self._attrs
        if name in self._attrs:
            raise HTMLTagAttrLookupError(f'name = {name!r}, attrs = {attrs!r}')
        self._attrs[name] = value

    def addChild(self, child):
        """Add a child to the receiver.

        The child will be another tag or a string (CDATA).
        """
        if not isinstance(child, (str, HTMLTag)):
            raise HTMLTagError(f'Invalid child: {child!r}')
        self._children.append(child)
        if isinstance(child, HTMLTag):
            self._subtags.append(child)

    # endregion Init and reading

    # region Access

    def name(self):
        return self._name

    def attr(self, name, default=NoDefault):
        if default is NoDefault:
            return self._attrs[name]
        return self._attrs.get(name, default)

    def hasAttr(self, name):
        return name in self._attrs

    def attrs(self):
        return self._attrs

    def numAttrs(self):
        return len(self._attrs)

    def childAt(self, index):
        return self._children[index]

    def numChildren(self):
        return len(self._children)

    def children(self):
        return self._children

    def subtagAt(self, index):
        return self._subtags[index]

    def numSubtags(self):
        return len(self._subtags)

    def subtags(self):
        return self._subtags

    # endregion Access

    # region Printing

    def pprint(self, out=None, indent=0):
        if out is None:
            out = sys.stdout
        wr = out.write
        spacer = ' '*4*indent
        wr(f'{spacer}<{self._name}>\n')
        for key, value in self._attrs.items():
            wr(f'{spacer}  {key.ljust(12)} = {value}\n')
        indent += 1
        for child in self._children:
            if isinstance(child, HTMLTag):
                child.pprint(out, indent)
            else:
                wr(f'{spacer}    {child}\n')
        wr(f'{spacer}</{self._name}>\n')

    def __repr__(self):
        r = ['<', self._name]
        attrs = self._attrs
        if attrs:
            for key in sorted(attrs):
                r.extend([' ', key, '="', attrs[key], '"'])
        r.append('>')
        if self._lineNumber or self._isClosed:
            r.append(' (')
            if self._lineNumber:
                r.append(str(self._lineNumber))
            if self._isClosed:
                if self._lineNumber:
                    r.append('; ')
                r.append(f'closed by {self._closedBy} at {self._closedAt}')
            r.append(')')
        r = ''.join(r)
        return r

    # endregion Printing

    # region Searching

    def tagWithMatchingAttr(self, name, value, default=NoDefault):
        """Search for tag with matching attributes.

        Performs a depth-first search for a tag with an attribute that matches
        the given value. If the tag cannot be found, a KeyError will be raised
        *unless* a default value was specified, which is then returned.

        Example::

            tag = tag.tagWithMatchingAttr('bgcolor', '#FFFFFF', None)
        """
        tag = self._tagWithMatchingAttr(name, value)
        if tag is None:
            if default is NoDefault:
                raise HTMLTagAttrLookupError(
                    'name = {name!r}, value = {value!r}')
            return default
        return tag

    def tagWithId(self, id_, default=NoDefault):
        """Search for tag with a given id.

        Finds and returns the tag with the given id. As in::

            <td id=foo> bar </td>

        This is just a cover for::

            tagWithMatchingAttr('id', id_, default)

        But searching for id's is so popular (at least in regression testing
        web sites) that this convenience method is provided.
        Why is it so popular? Because by attaching ids to logical portions
        of your HTML, your regression test suite can quickly zero in on them
        for examination.
        """
        return self.tagWithMatchingAttr('id', id_, default)

    # endregion Printing

    # region Parsing (HTMLReader)

    def closedBy(self, name, lineNumber):

        self._isClosed = True
        self._closedBy = name
        self._closedAt = lineNumber

    # endregion Parsing (HTMLReader)

    # region Self utility

    def _tagWithMatchingAttr(self, name, value):
        """Search for tag with matching attributes.

        Performs a depth-first search for a tag with an attribute that matches
        the given value. Returns None if the tag cannot be found. The method
        `tagWithMatchingAttr()` (e.g., sans underscore) is more commonly used.
        """
        if self._attrs.get(name) == value:
            return self
        for tag in self._subtags:
            matchingTag = tag._tagWithMatchingAttr(name, value)
            if matchingTag:
                return matchingTag
        return None

    # endregion Self utility


class HTMLReader(HTMLParser):
    """Reader class for representing HTML as tag objects.

    NOTES

    * Special attention is required regarding tags like ``<p>`` and ``<li>``
      which sometimes are closed and sometimes not. HTMLReader can deal with
      both situations (closed and not) provided that:

      * the file doesn't change conventions for a given tag
      * the reader knows ahead of time what to expect

    Be default, `HTMLReader` assumes that ``<p>`` and ``<li>`` will be closed
    with ``</p>`` and ``</li>`` as the official HTML spec encourages.

    But if your files don't close certain tags that are supposed to be
    required, you can do this::

        HTMLReader(extraEmptyTags=['p', 'li'])

    or::

        reader.extendEmptyTags(['p', 'li'])

    or just set them entirely::

        HTMLReader(emptyTags=['br', 'hr', 'p'])
        reader.setEmptyTags(['br', 'hr', 'p'])

    Although there are quite a few. Consider the DefaultEmptyTags global
    list (which is used to initialize the reader's tags) which contains
    about 16 tag names.

    If an HTML file doesn't conform to the reader's expectation, you will get
    an exception (see more below for details).

    If your HTML file doesn't contain root ``<html> ... </html>`` tags wrapping
    everything, a fake root tag will be constructed for you, unless you pass
    in fakeRootTagIfNeeded=False.

    Besides fixing your reader manually, you could conceivably loop through
    the permutations of the various empty tags to see if one of them resulted
    in a correct read.

    Or you could fix the HTML.

      * The reader ignores extra preceding and trailing whitespace by stripping
        it from strings. I suppose this is a little harsher than reducing spans
        of preceding and trailing whitespace down to one space, which is what
        really happens in an HTML browser.

      * The reader will not read past the closing ``</html>`` tag.

      * The reader is picky about the correctness of the HTML you feed it.
        If tags are not closed, overlap (instead of nest) or left unfinished,
        an exception is thrown. These include `HTMLTagUnbalancedError`,
        `HTMLTagIncompleteError` and `HTMLNotAllowedError` which all inherit
        `HTMLTagError`.

        This pickiness can be quite useful for the validation of the HTML of
        your own applications.
    """

    # region Init

    def __init__(
            self, emptyTags=None, extraEmptyTags=None,
            fakeRootTagIfNeeded=True):
        super().__init__()
        self._filename = None
        self._rootTag = None
        self._fakeRootTagIfNeeded = fakeRootTagIfNeeded
        self._usedFakeRootTag = False
        self._tagStack = []
        self._finished = False

        # Options
        self._printsStack = False
        self._ignoreWS = True
        self._endingTag = 'html'

        # Handle optional args
        if emptyTags is not None:
            self.setEmptyTags(emptyTags)
        else:
            self.setEmptyTags(DefaultEmptyTags)
        if extraEmptyTags is not None:
            self.extendEmptyTags(extraEmptyTags)

    # endregion Init

    # region Reading

    def readFileNamed(self, filename, retainRootTag=True):
        """Read the given file.

        Relies on readString(). See that method for more information.
        """
        self._filename = filename
        with open(filename) as f:
            contents = f.read()
        return self.readString(contents, retainRootTag)

    def readString(self, string, retainRootTag=True):
        """Read the given string, store the results and return the root tag.

        You could continue to use HTMLReader object or disregard it and simply
        use the root tag.
        """
        self._rootTag = None
        self._tagStack = []
        self._finished = False
        self.reset()
        self._lineNumber = 1
        self.computeTagContainmentConfig()
        try:
            for line in string.splitlines():
                self.feed(line + '\n')
                self._lineNumber += 1
            self.close()
        finally:
            self.reset()
        if retainRootTag:
            return self._rootTag
        tag = self._rootTag
        self._rootTag = None
        return tag

    # endregion Reading

    # region Printing

    def pprint(self, out=None):
        """Pretty prints the tag, its attributes and all its children.

        Indentation is used for subtags.
        Print 'Empty.' if there is no root tag.
        """
        if self._rootTag:
            self._rootTag.pprint(out)
        else:
            if out is None:
                out = sys.stdout
            out.write('Empty.')

    # endregion Printing

    # region Access

    def rootTag(self):
        """Return the root tag.

        May return None if no HTML has been read yet, or if the last
        invocation of one of the read methods was passed retainRootTag=False.
        """
        return self._rootTag

    def filename(self):
        """Return the name of the file if one has been read, otherwise None."""
        return self._filename

    def emptyTags(self):
        """Return a list of empty tags.

        See also: class docs and setEmptyTags().
        """
        return self._emptyTagList

    def setEmptyTags(self, tagList):
        """Set the HTML tags that are considered empty such as <br> and <hr>.

        The default is found in the global, DefaultEmptyTags, and is fairly
        thorough, but does not include <p>, <li> and some other tags that
        HTML authors often use as empty tags.
        """
        self._emptyTagList = list(tagList)
        self._updateEmptyTagSet()

    def extendEmptyTags(self, tagList):
        """Extend the current list of empty tags with the given list."""
        self._emptyTagList.extend(tagList)
        self._updateEmptyTagSet()

    # endregion Access

    # region Debugging

    def error(self, message):
        raise RuntimeError(f'HTMLReader error: {message}')

    def printsStack(self):
        return self._printsStack

    def setPrintsStack(self, flag):
        """Set the boolean value of the "prints stack" option.

        This is a debugging option which will print the internal tag stack
        during HTML processing. The default value is False.
        """
        self._printsStack = flag

    # endregion Debugging

    # region Command line

    def main(self, args=None):
        """The command line equivalent of readFileNamed().

        Invoked when HTMLTag is run as a program.
        """
        if args is None:
            args = sys.argv
        if len(args) < 2:
            self.usage()
        return self.readFileNamed(args[1])

    def usage(self):
        print('HTMLTag: usage:  HTMLTag <html file>')
        sys.exit(1)

    # endregion Command line

    # region HTMLParser handlers

    def handle_data(self, data):
        if self._finished:
            return
        if not isinstance(data, str):
            raise HTMLTagError(f'Encountered non-string data: {data!r}')
        if self._ignoreWS:
            data = data.strip()
            if not data:
                return
        if self._tagStack:
            self._tagStack[-1].addChild(data)
        else:
            print(f'<> data={data!r}')

    def handle_pi(self, data):
        raise HTMLTagProcessingInstructionError(
            f'Was not expecting a processing instruction: {data!r}')

    def handle_starttag(self, name, attrs):  # pylint: disable=arguments-differ
        if self._finished:
            return
        tag = HTMLTag(name, lineNumber=self._lineNumber)
        for attrName, value in attrs:
            tag.readAttr(attrName, value)
        if name in self._emptyTagSet:
            # We'll never have any children. Boo hoo.
            if not self._rootTag:
                raise HTMLTagError(
                    f'Cannot start HTML with an empty tag: {tag!r}')
            self._tagStack[-1].addChild(tag)
            empty = True
        else:
            # We could have children, so we go on the stack
            # Also, if this is the first tag, then make it the root.
            # If it's the first tag and it isn't an <html> tag,
            # create a fake "container" html tag.
            if self._tagStack:
                lastTag = self._tagStack[-1]
                # is this legal?
                tagConfig = self._tagContainmentConfig.get(lastTag.name())
                if tagConfig:
                    tagConfig.encounteredTag(name, self._lineNumber)
                # tell last tag about his new child
                lastTag.addChild(tag)
            elif name != 'html' and self._fakeRootTagIfNeeded:
                self._rootTag = HTMLTag('html')
                self._tagStack.append(self._rootTag)
                self._tagStack[-1].addChild(tag)
                self._usedFakeRootTag = True
            else:
                self._rootTag = tag
            self._tagStack.append(tag)
            empty = False
        if self._printsStack:
            prefix = ('START', '-----')[empty]
            print(f'{prefix} {name.ljust(6)}: {self._tagStack!r}')

    def handle_endtag(self, name):  # pylint: disable=arguments-differ
        if self._finished:
            return
        if name == self._endingTag:
            self._finished = True
        openingTag = self._tagStack.pop()
        if self._printsStack:
            print(f'END   {name.ljust(6)}: {self._tagStack}')
        if openingTag.name() != name:
            raise HTMLTagUnbalancedError(
                f'line {self._lineNumber}:'
                f' opening is {openingTag}, but closing is <{name}>.',
                line=self._lineNumber, opening=openingTag.name(),
                closing=name, tagStack=self._tagStack)
        openingTag.closedBy(name, self._lineNumber)

    def close(self):
        stackSize = len(self._tagStack)
        if stackSize > 0 and not (stackSize == 1 and self._usedFakeRootTag):
            raise HTMLTagIncompleteError(
                f'line {self._lineNumber}: tagStack = {self._tagStack!r}',
                line=self._lineNumber, tagStack=repr(self._tagStack))
        super().close()

    # endregion HTMLParser handlers

    # region Self utility

    def _updateEmptyTagSet(self):
        """Create a set out of the empty tag list for quick look up."""
        self._emptyTagSet = set(self._emptyTagList)

    # The following dict defines for various tags either:
    #    + the complete set of tags that can be contained within
    #    - a set of tags that cannot be contained within
    # This information helps HTMLReader detect some types of errors
    # earlier and other types of errors, it would never detect.
    tagContainmentConfig = {
        'html':   'canOnlyHave head body',
        'head':   'cannotHave  html head body',
        'body':   'cannotHave  html head body',
        'table':  'canOnlyHave tr thead tbody tfoot a',
        'tr':     'canOnlyHave th td',
        'td':     'cannotHave  td tr',
        'select': 'canOnlyHave option',
    }

    def computeTagContainmentConfig(self):
        config = {}
        for key, value in self.tagContainmentConfig.items():
            if isinstance(value, str):
                value = value.split()
                configClass = configClassForName.get(value.pop(0))
                if configClass is None:
                    raise KeyError(
                        f'Unknown config name {key!r} for value {value!r}'
                        f' in {self.__class__.__name__}.tagContainmentConfig')
                config[key] = configClass(key, value)
            else:
                if not isinstance(value, TagConfig):
                    raise TypeError(f'key={key!r}, value={value!r}')
                config[key] = value
        self._tagContainmentConfig = config

    # endregion Self utility


class TagConfig:

    def __init__(self, name, tags):
        self.name = name
        # turn tag list into a set for fast lookup (avoid linear searches)
        self.tags = set(tags)

    def encounteredTag(self, tag, lineNum):
        raise AbstractError(self.__class__)


class TagCanOnlyHaveConfig(TagConfig):

    def encounteredTag(self, tag, lineNum):
        if tag.lower() not in self.tags:
            raise HTMLNotAllowedError(
                f'line {lineNum}: the tag {tag!r} is not allowed in'
                f' {self.name!r} which can only have {sorted(self.tags)!r}.',
                line=lineNum, encounteredTag=tag, containingTag=self.name,
                canOnlyHave=self.tags)


class TagCannotHaveConfig(TagConfig):

    def encounteredTag(self, tag, lineNum):
        if tag.lower() in self.tags:
            raise HTMLNotAllowedError(
                f'line {lineNum}: The tag {tag!r} is not allowed in'
                ' {self.name!r} which cannot have {sorted(self.tags!r}.',
                line=lineNum, enounteredTag=tag, containingTag=self.name,
                cannotHave=self.tags)


configClassForName = dict(
    canOnlyHave=TagCanOnlyHaveConfig, cannotHave=TagCannotHaveConfig)


if __name__ == '__main__':
    html = HTMLReader().main()
    html.pprint()
