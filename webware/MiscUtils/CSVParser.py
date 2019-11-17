"""CSVParser.py

A parser for CSV files.
"""

# The states of the parser
(StartRecord, StartField, InField, QuoteInField,
 InQuotedField, QuoteInQuotedField, EndQuotedField) = range(7)

# State handlers can return Finished to terminate parsing early
Finished = 10


class ParseError(Exception):
    """CSV file parse error."""


class CSVParser:
    """Parser for CSV files.

    Parses CSV files including all subtleties such as:

    * commas in fields
    * double quotes in fields
    * embedded newlines in fields

    Examples of programs that produce such beasts include MySQL and Excel.

    For a higher-level, friendlier CSV class with many conveniences,
    see `DataTable` (which uses this class for its parsing).

    Example::

        records = []
        parse = CSVParser().parse
        for line in lines:
            results = parse(line)
            if results is not None:
                records.append(results)


    CREDIT

    The algorithm was taken directly from the open source Python
    C-extension, csv: https://www.object-craft.com.au/projects/csv/

    It would be nice to use the csv module when present, since it is
    substantially faster. Before that can be done, it needs to support
    `allowComments` and `stripWhitespace`, and pass the TestCSVParser.py
    test suite.
    """

    def __init__(
            self, allowComments=True, stripWhitespace=True, fieldSep=',',
            autoReset=True, doubleQuote=True):
        """Create a new CSV parser.

        `allowComments`:
          If true (the default), then comment lines using the Python comment
          marker are allowed.
        `stripWhitespace`:
          If true (the default), then left and right whitespace is stripped
          off from all fields.
        `fieldSep`:
          Defines the field separator string (a comma by default).
        `autoReset`:
          If true (the default), recover from errors automatically.
        `doubleQuote`:
          If true (the default), assume quotes in fields are escaped by
          appearing doubled.
        """
        # settings
        self._allowComments = allowComments
        self._stripWhitespace = stripWhitespace
        self._doubleQuote = doubleQuote
        self._fieldSep = fieldSep
        self._autoReset = autoReset

        # Other
        self._state = StartRecord
        self._fields = []
        self._hadParseError = False
        self._field = []  # a list of chars for the cur field
        self.addChar = self._field.append

        # The handlers for the various states
        self._handlers = [
            self.startRecord,
            self.startField,
            self.inField,
            self.quoteInField,
            self.inQuotedField,
            self.quoteInQuotedField,
            self.endQuotedField,
        ]

    # region Parse

    def parse(self, line):
        """Parse a single line and return a list of string fields.

        Returns None if the CSV record contains embedded newlines and
        the record is not yet complete.
        """
        if self._autoReset and self._hadParseError:
            self.reset()
        handlers = self._handlers

        i = 0
        lineLen = len(line)
        while i < lineLen:
            c = line[i]
            if c == '\r':
                i += 1
                if i == lineLen:
                    break  # Mac end of line
                c = line[i]
                if c == '\n':
                    i += 1
                    if i == lineLen:
                        break  # Win end of line

                self._hadParseError = True
                raise ParseError('Newline inside string')

            if c == '\n':
                i += 1
                if i == lineLen:
                    break  # Unix end of line

                self._hadParseError = True
                raise ParseError('Newline inside string')

            if handlers[self._state](c) == Finished:
                break  # process a character

            i += 1

        handlers[self._state]('\0')  # signal the end of the input

        if self._state == StartRecord:
            fields = self._fields
            self._fields = []
            if self._stripWhitespace:
                fields = [field.strip() for field in fields]
            return fields

        return None  # indicates multi-line record; e.g. not finished

    # endregion Parse

    # region Reset

    def reset(self):
        """Reset the parser.

        Resets the parser to a fresh state in order to recover from
        exceptions. But if autoReset is true (the default), this is
        done automatically.
        """
        self._fields = []
        self._state = StartRecord
        self._hadParseError = False

    # endregion Reset

    # region State Handlers

    def startRecord(self, c):
        if c != '\0':  # not empty line
            if c == '#' and self._allowComments:
                return Finished
            self._state = StartField
            self.startField(c)

    def startField(self, c):
        if c == '"':
            self._state = InQuotedField  # start quoted field
        elif c == self._fieldSep:
            self.saveField()  # save empty field
        elif c == ' ' and self._stripWhitespace:
            pass  # skip over preceding whitespace
        elif c == '\0':
            self.saveField()  # save empty field
            self._state = StartRecord
        else:
            self.addChar(c)  # begin new unquoted field
            self._state = InField

    def inField(self, c):
        # in unquoted field
        if c == self._fieldSep:
            self.saveField()
            self._state = StartField
        elif c == '\0':
            self.saveField()  # end of line
            self._state = StartRecord
        elif c == '"' and self._doubleQuote:
            self._state = QuoteInField
        else:
            self.addChar(c)  # normal character

    def quoteInField(self, c):
        self.addChar('"')
        if c == '"':
            self._state = InField  # save "" as "
        elif c == '\0':
            self.saveField()  # end of line
            self._state = StartRecord
        elif c == self._fieldSep:
            self.saveField()
            self._state = StartField
        else:
            self.addChar(c)  # normal character
            self._state = InField

    def inQuotedField(self, c):
        if c == '"':
            if self._doubleQuote:
                self._state = QuoteInQuotedField
            else:
                self.saveField()  # end of field
                self._state = EndQuotedField
        elif c == '\0':
            self.addChar('\n')  # end of line
        else:
            self.addChar(c)  # normal character

    def quoteInQuotedField(self, c):
        if c == '"':
            self.addChar('"')  # save "" as "
            self._state = InQuotedField
        elif c == self._fieldSep:
            self.saveField()
            self._state = StartField
        elif c == ' ' and self._stripWhitespace:
            pass  # skip it
        elif c == '\0':
            self.saveField()  # end of line
            self._state = StartRecord
        else:
            self._hadParseError = True  # illegal
            raise ParseError(f'{self._fieldSep} expected after "')

    def endQuotedField(self, c):
        if c == self._fieldSep:  # seen closing " on quoted field
            self._state = StartField  # wait for new field
        elif c == '\0':
            self._state = StartRecord  # end of line
        else:
            self._hadParseError = True
            raise ParseError(f'{self._fieldSep} expected after "')

    def saveField(self):
        self._fields.append(''.join(self._field))
        self._field = []
        self.addChar = self._field.append

    # endregion State Handlers


# Call the global function parse() if you like the default settings
_parser = CSVParser()
parse = _parser.parse
