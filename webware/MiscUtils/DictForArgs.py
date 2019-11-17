"""DictForArgs.py

See the doc string for the dictForArgs() function.

Also, there is a test suite in Tests/TestDictForArgs.py
"""

import re


class DictForArgsError(Exception):
    """Error when building dictionary from arguments."""


def _SyntaxError(s):
    raise DictForArgsError('Syntax error: %r' % s)


_nameRE = re.compile(r'\w+')
_equalsRE = re.compile(r'\=')
_stringRE = re.compile(r'''"[^"]+"|'[^']+'|\S+''')
_whiteRE = re.compile(r'\s+')

_REs = [_nameRE, _equalsRE, _stringRE, _whiteRE]


def dictForArgs(s):
    """Build dictionary from arguments.

    Takes an input such as::

        x=3
        name="foo"
        first='john' last='doe'
        required border=3

    And returns a dictionary representing the same. For keys that aren't
    given an explicit value (such as 'required' above), the value is '1'.

    All values are interpreted as strings. If you want ints and floats,
    you'll have to convert them yourself.

    This syntax is equivalent to what you find in HTML and close to other
    ML languages such as XML.

    Returns {} for an empty string.

    The informal grammar is::

        (NAME [=NAME|STRING])*

    Will raise DictForArgsError if the string is invalid.

    See also: pyDictForArgs() and expandDictWithExtras() in this module.
    """

    s = s.strip()

    # Tokenize

    verbose = False
    matches = []
    start = 0
    sLen = len(s)

    if verbose:
        print(f'>> dictForArgs({s!r})')
        print('>> sLen:', sLen)
    while start < sLen:
        for regEx in _REs:
            if verbose:
                print('>> try:', regEx)
            match = regEx.match(s, start)
            if verbose:
                print('>> match:', match)
            if match is not None:
                if match.re is not _whiteRE:
                    matches.append(match)
                start = match.end()
                if verbose:
                    print('>> new start:', start)
                break
        else:
            _SyntaxError(s)

    if verbose:
        names = []
        for match in matches:
            if match.re is _nameRE:
                name = 'name'
            elif match.re is _equalsRE:
                name = 'equals'
            elif match.re is _stringRE:
                name = 'string'
            elif match.re is _whiteRE:
                name = 'white'
            names.append(name)
        print('>> names =', names)

    # Process tokens

    # At this point we have a list of all the tokens (as re.Match objects)
    # We need to process these into a dictionary.

    d = {}
    matchesLen = len(matches)
    i = 0
    while i < matchesLen:
        match = matches[i]
        if i + 1 < matchesLen:
            peekMatch = matches[i+1]
        else:
            peekMatch = None
        if match.re is _nameRE:
            if peekMatch is not None:
                if peekMatch.re is _nameRE:
                    # We have a name without an explicit value
                    d[match.group()] = '1'
                    i += 1
                    continue
                if peekMatch.re is _equalsRE:
                    if i + 2 < matchesLen:
                        target = matches[i+2]
                        if target.re is _nameRE or target.re is _stringRE:
                            value = target.group()
                            if value[0] == "'" or value[0] == '"':
                                value = value[1:-1]
                            d[match.group()] = value
                            i += 3
                            continue
            else:
                d[match.group()] = '1'
                i += 1
                continue
        _SyntaxError(s)

    if verbose:
        print()

    return d


def pyDictForArgs(s):
    """Build dictionary from arguments.

    Takes an input such as::

        x=3
        name="foo"
        first='john'; last='doe'
        list=[1, 2, 3]; name='foo'

    And returns a dictionary representing the same.

    All values are interpreted as Python expressions. Any error in these
    expressions will raise the appropriate Python exception. This syntax
    allows much more power than dictForArgs() since you can include
    lists, dictionaries, actual ints and floats, etc.

    This could also open the door to hacking your software if the input
    comes from a tainted source such as an HTML form or an unprotected
    configuration file.

    Returns {} for an empty string.

    See also: dictForArgs() and expandDictWithExtras() in this module.
    """
    if s:
        s = s.strip()
    if not s:
        return {}

    # special case: just a name
    # meaning: name=1
    # example: isAbstract
    if ' ' not in s and '=' not in s and s[0].isalpha():
        s += '=1'

    results = {}
    exec(s, results)

    del results['__builtins__']
    return results


def expandDictWithExtras(d, key='Extras',
                         delKey=True, dictForArgs=dictForArgs):
    """Return a dictionary with the 'Extras' column expanded by dictForArgs().

    For example, given::

        {'Name': 'foo', 'Extras': 'x=1 y=2'}

    The return value is::

        {'Name': 'foo', 'x': '1', 'y': '2'}

    The key argument controls what key in the dictionary is used to hold
    the extra arguments. The delKey argument controls whether that key and
    its corresponding value are retained.
    The same dictionary may be returned if there is no extras key.
    The most typical use of this function is to pass a row from a DataTable
    that was initialized from a CSV file (e.g., a spreadsheet or tabular file).
    FormKit and MiddleKit both use CSV files and allow for an Extras column
    to specify attributes that occur infrequently.
    """
    if key in d:
        newDict = dict(d)
        if delKey:
            del newDict[key]
        newDict.update(dictForArgs(d[key]))
        return newDict
    return d


# old (deprecated) aliases
DictForArgs, PyDictForArgs, ExpandDictWithExtras = (
    dictForArgs, pyDictForArgs, expandDictWithExtras)
