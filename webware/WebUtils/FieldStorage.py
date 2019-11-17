"""FieldStorage.py

This module defines a subclass of the standard Python cgi.FieldStorage class
with an extra method that will allow a FieldStorage to parse a query string
even in a POST request.
"""

import cgi
import os

from collections import defaultdict
from urllib import parse


class FieldStorage(cgi.FieldStorage):
    """Modified FieldStorage class for POST requests with query strings.

    Parameters in the query string which have not been sent via POST are
    appended to the field list. This is different from the behavior of
    Python versions before 2.6 which completely ignored the query string in
    POST request, but it's also different from the behavior of the later Python
    versions which append values from the query string to values sent via POST
    for parameters with the same name. With other words, our FieldStorage class
    overrides the query string parameters with the parameters sent via POST.

    As recommended by W3C in section B.2.2 of the HTML 4.01 specification,
    we also support use of ';' in place of '&' as separator in query strings.
    """

    def __init__(self, fp=None, headers=None, outerboundary=b'',
                 environ=None, keep_blank_values=False,
                 strict_parsing=False, limit=None,
                 encoding='utf-8', errors='replace', max_num_fields=None):
        if environ is None:
            environ = os.environ
        method = environ.get('REQUEST_METHOD', 'GET').upper()
        qs_on_post = None if method in ('GET', 'HEAD') else environ.get(
            'QUERY_STRING', None)
        if qs_on_post:
            environ['QUERY_STRING'] = ''
        try:
            if headers is None:
                # work around Python issue 27777 in FieldStorage
                content_type = environ.get('CONTENT_TYPE')
                if (content_type and
                        content_type != 'application/x-www-form-urlencoded'
                        and not content_type.startswith('multipart/')):
                    if 'CONTENT_LENGTH' in environ:
                        headers = {'content-type': content_type,
                                   'content-length': '-1'}
            if max_num_fields is None:
                # max_num_fields is only supported since Python 3.6.7 and 3.7.2
                super().__init__(
                    fp, headers=headers, outerboundary=outerboundary,
                    environ=environ, keep_blank_values=keep_blank_values,
                    strict_parsing=strict_parsing, limit=limit,
                    encoding=encoding, errors=errors)
            else:
                super().__init__(
                    fp, headers=headers, outerboundary=outerboundary,
                    environ=environ, keep_blank_values=keep_blank_values,
                    strict_parsing=strict_parsing, limit=limit,
                    encoding=encoding, errors=errors,
                    max_num_fields=max_num_fields)
        finally:
            if qs_on_post:
                environ['QUERY_STRING'] = qs_on_post
        if qs_on_post:
            self.add_qs(qs_on_post)

    def add_qs(self, qs):
        """Add all non-existing parameters from the given query string."""
        values = defaultdict(list)
        for name_values in qs.split('&'):
            for name_value in name_values.split(';'):
                nv = name_value.split('=', 2)
                if len(nv) != 2:
                    if self.strict_parsing:
                        raise ValueError(f'bad query field: {name_value!r}')
                    continue
                name = parse.unquote(nv[0].replace('+', ' '))
                value = parse.unquote(nv[1].replace('+', ' '))
                if len(value) or self.keep_blank_values:
                    values[name].append(value)
        if self.list is None:
            # This makes sure self.keys() are available, even
            # when valid POST data wasn't encountered.
            self.list = []
        for key in values:
            if key not in self:
                # Only append values that aren't already the FieldStorage;
                # this makes POSTed vars override vars on the query string.
                for value in values[key]:
                    self.list.append(cgi.MiniFieldStorage(key, value))
