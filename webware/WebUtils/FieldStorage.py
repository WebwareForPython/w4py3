"""FieldStorage.py

This module provides that latest version of the now deprecated standard Python
cgi.FieldStorage class with a slight modification so that fields passed in the
body of a POST request override any fields passed in the query string.
"""

import locale
import os
import re
import sys
import tempfile

from collections.abc import Mapping
from io import StringIO, BytesIO, TextIOWrapper
from email.parser import FeedParser
from email.message import Message
from urllib.parse import parse_qsl

maxlen = 0  # unlimited input


class FieldStorage:
    """Store a sequence of fields, reading multipart/form-data.

    This is a slightly modified version of the FieldStorage class
    in the now deprecated cgi module of the standard library.

    This class provides naming, typing, files stored on disk, and
    more.  At the top level, it is accessible like a dictionary, whose
    keys are the field names.  (Note: None can occur as a field name.)
    The items are either a Python list (if there's multiple values) or
    another FieldStorage or MiniFieldStorage object.  If it's a single
    object, it has the following attributes:

    name: the field name, if specified; otherwise None
    filename: the filename, if specified; otherwise None;
    this is the client side filename, *not* the file name on which
    it is stored (that's a temporary file you don't deal with)

    value: the value as a *string*; for file uploads, this transparently
    reads the file every time you request the value and returns *bytes*

    file: the file(-like) object from which you can read the data *as bytes*;
    None if the data is stored a simple string

    type: the content-type, or None if not specified

    type_options: dictionary of options specified on the content-type line

    disposition: content-disposition, or None if not specified

    disposition_options: dictionary of corresponding options

    headers: a dictionary(-like) object (sometimes email.message.Message
    or a subclass thereof) containing *all* headers

    The class can be subclassed, mostly for the purpose of overriding
    the make_file() method, which is called internally to come up with
    a file open for reading and writing.  This makes it possible to
    override the default choice of storing all files in a temporary
    directory and unlinking them as soon as they have been opened.

    Parameters in the query string which have not been sent via POST are
    appended to the field list. This is different from the behavior of
    Python versions before 2.6 which completely ignored the query string in
    POST request, but it's also different from the behavior of the later Python
    versions which append values from the query string to values sent via POST
    for parameters with the same name. With other words, our FieldStorage class
    overrides the query string parameters with the parameters sent via POST.
    """
    def __init__(self, fp=None, headers=None, outerboundary=b'',
                 environ=None, keep_blank_values=False, strict_parsing=False,
                 limit=None, encoding='utf-8', errors='replace',
                 max_num_fields=None, separator='&'):
        """Constructor.  Read multipart/* until last part.
        Arguments, all optional:
        fp: file pointer; default: sys.stdin.buffer

        Not used when the request method is GET.
        Can be a TextIOWrapper object or an object whose read() and readline()
        methods return bytes.

        headers: header dictionary-like object;
        default: taken from environ as per CGI spec

        outerboundary: terminating multipart boundary (for internal use only)

        environ: environment dictionary; default: os.environ

        keep_blank_values: flag indicating whether blank values in
        percent-encoded forms should be treated as blank strings.
        A true value indicates that blanks should be retained as blank strings.
        The default false value indicates that blank values are to be ignored
        and treated as if they were not included.

        strict_parsing: flag indicating what to do with parsing errors.
        If false (the default), errors are silently ignored.
        If true, errors raise a ValueError exception.

        limit: used internally to read parts of multipart/form-data forms,
        to exit from the reading loop when reached. It is the difference
        between the form content-length and the number of bytes already read.

        encoding, errors: the encoding and error handler used to decode the
        binary stream to strings. Must be the same as the charset defined for
        the page sending the form (content-type : meta http-equiv or header)

        max_num_fields: int. If set, then __init__ throws a ValueError if
        there are more than n fields read by parse_qsl().
        """
        method = 'GET'
        self.keep_blank_values = keep_blank_values
        self.strict_parsing = strict_parsing
        self.max_num_fields = max_num_fields
        self.separator = separator
        if environ is None:
            environ = os.environ
        if 'REQUEST_METHOD' in environ:
            method = environ['REQUEST_METHOD'].upper()
        self.qs_on_post = None
        if method in ('GET', 'HEAD'):
            if 'QUERY_STRING' in environ:
                qs = environ['QUERY_STRING']
            elif sys.argv[1:]:
                qs = sys.argv[1]
            else:
                qs = ''
            qs = qs.encode(locale.getpreferredencoding(), 'surrogateescape')
            fp = BytesIO(qs)
            if headers is None:
                headers = {'content-type': 'application/x-www-form-urlencoded'}
        if headers is None:
            headers = {}
            if method == 'POST':
                headers['content-type'] = 'application/x-www-form-urlencoded'
            if 'CONTENT_TYPE' in environ:
                headers['content-type'] = environ['CONTENT_TYPE']
            if 'QUERY_STRING' in environ:
                self.qs_on_post = environ['QUERY_STRING']
            if 'CONTENT_LENGTH' in environ:
                headers['content-length'] = environ['CONTENT_LENGTH']
        else:
            if not (isinstance(headers, (Mapping, Message))):
                raise TypeError(
                    'headers must be mapping or an instance of'
                    ' email.message.Message')
        self.headers = headers
        if fp is None:
            self.fp = sys.stdin.buffer
        elif isinstance(fp, TextIOWrapper):
            self.fp = fp.buffer
        else:
            if not (hasattr(fp, 'read') and hasattr(fp, 'readline')):
                raise TypeError('fp must be file pointer')
            self.fp = fp

        self.encoding = encoding
        self.errors = errors

        if not isinstance(outerboundary, bytes):
            type_name = type(outerboundary).__name__
            raise TypeError(f'outerboundary must be bytes, not {type_name}')
        self.outerboundary = outerboundary

        self.bytes_read = 0
        self.limit = limit

        cdisp, pdict = '', {}
        if 'content-disposition' in self.headers:
            cdisp, pdict = parse_header(self.headers['content-disposition'])
        self.disposition = cdisp
        self.disposition_options = pdict
        self.name = None
        if 'name' in pdict:
            self.name = pdict['name']
        self.filename = None
        if 'filename' in pdict:
            self.filename = pdict['filename']
        self._binary_file = self.filename is not None

        if 'content-type' in self.headers:
            ctype, pdict = parse_header(self.headers['content-type'])
        elif self.outerboundary or method != 'POST':
            ctype, pdict = 'text/plain', {}
        else:
            ctype, pdict = 'application/x-www-form-urlencoded', {}
        self.type = ctype
        self.type_options = pdict
        if not self._binary_file and isBinaryType(ctype, pdict):
            self._binary_file = True
        self.innerboundary = pdict['boundary'].encode(
            self.encoding, self.errors) if 'boundary' in pdict else b''

        clen = -1
        if 'content-length' in self.headers:
            try:
                clen = int(self.headers['content-length'])
            except ValueError:
                pass
            if maxlen and clen > maxlen:
                raise ValueError('Maximum content length exceeded')
        self.length = clen
        if self.limit is None and clen >= 0:
            self.limit = clen

        self.list = self.file = None
        self.done = 0
        if ctype == 'application/x-www-form-urlencoded':
            self.read_urlencoded()
        elif ctype[:10] == 'multipart/':
            self.read_multi(environ, keep_blank_values, strict_parsing)
        else:
            self.read_single()

    def __del__(self):
        try:
            self.file.close()
        except AttributeError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.file.close()

    def __repr__(self):
        """Return a printable representation."""
        return (
            f'FieldStorage({self.name!r}, {self.filename!r}, {self.value!r})')

    def __iter__(self):
        return iter(self.keys())

    def __getattr__(self, name):
        if name != 'value':
            raise AttributeError(name)
        if self.file:
            self.file.seek(0)
            value = self.file.read()
            self.file.seek(0)
        elif self.list is not None:
            value = self.list
        else:
            value = None
        return value

    def __getitem__(self, key):
        """Dictionary style indexing."""
        if self.list is None:
            raise TypeError('not indexable')
        found = [item for item in self.list if item.name == key]
        if not found:
            raise KeyError(key)
        if len(found) == 1:
            return found[0]
        return found

    def getvalue(self, key, default=None):
        """Dictionary style get() method, including 'value' lookup."""
        if key in self:
            value = self[key]
            if isinstance(value, list):
                return [x.value for x in value]
            return value.value
        return default

    def getfirst(self, key, default=None):
        """Return the first value received."""
        if key in self:
            value = self[key]
            if isinstance(value, list):
                return value[0].value
            return value.value
        return default

    def getlist(self, key):
        """Return list of received values."""
        if key in self:
            value = self[key]
            if isinstance(value, list):
                return [x.value for x in value]
            return [value.value]
        return []

    def keys(self):
        """Dictionary style keys() method."""
        if self.list is None:
            raise TypeError("not indexable")
        return list({item.name for item in self.list})

    def __contains__(self, key):
        """Dictionary style __contains__ method."""
        if self.list is None:
            raise TypeError('not indexable')
        return any(item.name == key for item in self.list)

    def __len__(self):
        """Dictionary style len(x) support."""
        return len(self.keys())

    def __bool__(self):
        if self.list is None:
            raise TypeError('Cannot be converted to bool.')
        return bool(self.list)

    def read_urlencoded(self):
        """Internal: read data in query string format."""
        qs = self.fp.read(self.length)
        if not isinstance(qs, bytes):
            type_name = type(qs).__name__
            raise ValueError(f'{self.fp} should return bytes, got {type_name}')
        qs = qs.decode(self.encoding, self.errors)
        kwargs = {
            'keep_blank_values': self.keep_blank_values,
            'strict_parsing': self.strict_parsing,
            'encoding': self.encoding, 'errors': self.errors}
        kwargs['max_num_fields'] = self.max_num_fields
        kwargs['separator'] = self.separator
        query = parse_qsl(qs, **kwargs)
        # contrary to the standard library, we only add those fields
        # from the query string that do not already appear in the body
        if self.qs_on_post:
            query_on_post = parse_qsl(self.qs_on_post, **kwargs)
            posted_names = {key for key, value in query}
            query.extend((key, value) for key, value in query_on_post
                         if key not in posted_names)
        self.list = [MiniFieldStorage(key, value) for key, value in query]
        self.skip_lines()

    FieldStorageClass = None

    def read_multi(self, environ, keep_blank_values, strict_parsing):
        """Internal: read a part that is itself multipart."""
        ib = self.innerboundary
        if not valid_boundary(ib):
            raise ValueError(f'Invalid boundary in multipart form: {ib!r}')
        self.list = []
        if self.qs_on_post:
            kwargs = {
                'keep_blank_values': self.keep_blank_values,
                'strict_parsing': self.strict_parsing,
                'encoding': self.encoding, 'errors': self.errors}
            kwargs['max_num_fields'] = self.max_num_fields
            kwargs['separator'] = self.separator
            query = parse_qsl(self.qs_on_post, **kwargs)
            self.list.extend(MiniFieldStorage(key, value)
                             for key, value in query)

        klass = self.FieldStorageClass or self.__class__
        first_line = self.fp.readline()
        if not isinstance(first_line, bytes):
            type_name = type(first_line).__name__
            raise ValueError(f'{self.fp} should return bytes, got {type_name}')
        self.bytes_read += len(first_line)

        while (first_line.strip() != (b'--' + self.innerboundary) and
                first_line):
            first_line = self.fp.readline()
            self.bytes_read += len(first_line)

        max_num_fields = self.max_num_fields
        if max_num_fields is not None:
            max_num_fields -= len(self.list)

        while True:
            parser = FeedParser()
            hdr_text = b''
            while True:
                data = self.fp.readline()
                hdr_text += data
                if not data.strip():
                    break
            if not hdr_text:
                break
            self.bytes_read += len(hdr_text)
            parser.feed(hdr_text.decode(self.encoding, self.errors))
            headers = parser.close()

            if 'content-length' in headers:
                del headers['content-length']

            limit = self.limit
            if limit is not None:
                limit -= self.bytes_read
            part = klass(self.fp, headers, ib, environ, keep_blank_values,
                         strict_parsing, limit, self.encoding, self.errors,
                         max_num_fields, self.separator)

            if max_num_fields is not None:
                max_num_fields -= 1
                if part.list:
                    max_num_fields -= len(part.list)
                if max_num_fields < 0:
                    raise ValueError('Max number of fields exceeded')

            self.bytes_read += part.bytes_read
            self.list.append(part)
            if part.done or self.bytes_read >= self.length > 0:
                break
        self.skip_lines()

    def read_single(self):
        """Internal: read an atomic part."""
        if self.length >= 0:
            self.read_binary()
            self.skip_lines()
        else:
            self.read_lines()
        self.file.seek(0)
        # contrary to the standard library, we also parse the query string
        if self.qs_on_post:
            kwargs = {
                'keep_blank_values': self.keep_blank_values,
                'strict_parsing': self.strict_parsing,
                'encoding': self.encoding, 'errors': self.errors}
            kwargs['max_num_fields'] = self.max_num_fields
            kwargs['separator'] = self.separator
            query = parse_qsl(self.qs_on_post, **kwargs)
            self.list = [MiniFieldStorage(key, value) for key, value in query]

    bufsize = 8 * 1024

    def read_binary(self):
        """Internal: read binary data."""
        todo = self.length
        while todo > 0:
            data = self.fp.read(min(todo, self.bufsize))
            if not isinstance(data, bytes):
                type_name = type(data).__name__
                raise ValueError(
                    f'{self.fp} should return bytes, got {type_name}')
            self.bytes_read += len(data)
            if not data:
                self.done = -1
                break
            if not self._binary_file:
                # fix for https://github.com/python/cpython/issues/71964
                try:
                    data = data.decode()
                except UnicodeDecodeError:
                    self._binary_file = True
            if self.file is None:
                self.file = self.make_file()
            self.file.write(data)
            todo -= len(data)

    def read_lines(self):
        """Internal: read lines until EOF or outerboundary."""
        self.file = self.__file = BytesIO(
            ) if self._binary_file else StringIO()
        if self.outerboundary:
            self.read_lines_to_outerboundary()
        else:
            self.read_lines_to_eof()

    def __write(self, line):
        """line is always bytes, not string"""
        if self.__file is not None:
            if self.__file.tell() + len(line) > 1000:
                self.file = self.make_file()
                data = self.__file.getvalue()
                self.file.write(data)
                self.__file = None
        if self._binary_file:
            self.file.write(line)
        else:
            self.file.write(line.decode(self.encoding, self.errors))

    def read_lines_to_eof(self):
        """Internal: read lines until EOF."""
        while True:
            line = self.fp.readline(1 << 16)
            self.bytes_read += len(line)
            if not line:
                self.done = -1
                break
            self.__write(line)

    def read_lines_to_outerboundary(self):
        """Internal: read lines until outerboundary.

        Data is read as bytes: boundaries and line ends must be converted
        to bytes for comparisons.
        """
        next_boundary = b"--" + self.outerboundary
        last_boundary = next_boundary + b'--'
        delim = b''
        last_line_lf_end = True
        _read = 0
        while True:
            if self.limit is not None and 0 <= self.limit <= _read:
                break
            line = self.fp.readline(1 << 16)
            self.bytes_read += len(line)
            _read += len(line)
            if not line:
                self.done = -1
                break
            if delim == b'\r':
                line = delim + line
                delim = b''
            if line.startswith(b'--') and last_line_lf_end:
                stripped_line = line.rstrip()
                if stripped_line == next_boundary:
                    break
                if stripped_line == last_boundary:
                    self.done = 1
                    break
            old_delim = delim
            if line.endswith(b'\r\n'):
                delim = b'\r\n'
                line = line[:-2]
                last_line_lf_end = True
            elif line.endswith(b'\n'):
                delim = b'\n'
                line = line[:-1]
                last_line_lf_end = True
            elif line.endswith(b'\r'):
                delim = b'\r'
                line = line[:-1]
                last_line_lf_end = False
            else:
                delim = b''
                last_line_lf_end = False
            self.__write(old_delim + line)

    def skip_lines(self):
        """Internal: skip lines until outer boundary if defined."""
        if not self.outerboundary or self.done:
            return
        next_boundary = b'--' + self.outerboundary
        last_boundary = next_boundary + b'--'
        last_line_lf_end = True
        while True:
            line = self.fp.readline(1 << 16)
            self.bytes_read += len(line)
            if not line:
                self.done = -1
                break
            if line.endswith(b'--') and last_line_lf_end:
                stripped_line = line.strip()
                if stripped_line == next_boundary:
                    break
                if stripped_line == last_boundary:
                    self.done = 1
                    break
            last_line_lf_end = line.endswith(b'\n')

    def make_file(self):
        """Overridable: return a readable & writable file.

        The file will be used as follows:
        - data is written to it
        - seek(0)
        - data is read from it
        The file is opened in binary mode for files, in text mode
        for other fields.
        This version opens a temporary file for reading and writing,
        and immediately deletes (unlinks) it.  The trick (on Unix!) is
        that the file can still be used, but it can't be opened by
        another process, and it will automatically be deleted when it
        is closed or when the current process terminates.
        If you want a more permanent file, you derive a class which
        overrides this method.  If you want a visible temporary file
        that is nevertheless automatically deleted when the script
        terminates, try defining a __del__ method in a derived class
        which unlinks the temporary files you have created.
        """
        if self._binary_file:
            return tempfile.TemporaryFile('wb+')
        return tempfile.TemporaryFile(
            'w+', encoding=self.encoding, newline='\n')


class MiniFieldStorage:
    """Like FieldStorage, for use when no file uploads are possible."""
    filename = None
    list = None
    type = None
    file = None
    type_options = {}
    disposition = None
    disposition_options = {}
    headers = {}

    def __init__(self, name, value):
        """Constructor from field name and value."""
        self.name = name
        self.value = value

    def __repr__(self):
        """Return printable representation."""
        return f'MiniFieldStorage({self.name!r}, {self.value!r})'


def parse_header(line):
    """Parse a Content-type like header.

    Return the main content-type and a dictionary of options.
    """
    parts = _parseparam(';' + line)
    key = parts.__next__()
    parsed_dict = {}
    for p in parts:
        p = p.split('=', 1)
        if len(p) > 1:
            name, value = p
            name = name.strip().lower()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1].replace('\\\\', '\\').replace('\\"', '"')
            parsed_dict[name] = value
    return key, parsed_dict


def _parseparam(s):
    while s[:1] == ';':
        s = s[1:]
        end = s.find(';')
        while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
            end = s.find(';', end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        yield f.strip()
        s = s[end:]


_vb_pattern = '^[ -~]{0,200}[!-~]$'
_vb_pattern_bytes = re.compile(_vb_pattern.encode('ascii'))
_vb_pattern_str = re.compile(_vb_pattern)


def valid_boundary(s):
    pattern = _vb_pattern_bytes if isinstance(s, bytes) else _vb_pattern_str
    return pattern.match(s)


def isBinaryType(ctype, pdict=None):
    """"Check whether the given MIME type uses binary data."""
    if pdict and pdict.get('charset') == 'binary':
        return True
    return not (
        ctype.startswith('text/') or ctype.endswith(('+json', '+xml')) or
        (ctype.startswith('application') and
         ctype.endswith(('/json', '/xml', '/ecmascript', '/javascript'))))
