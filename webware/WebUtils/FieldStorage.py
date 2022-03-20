"""FieldStorage.py

This module defines a subclass of the standard Python cgi.FieldStorage class
with an extra method that will allow a FieldStorage to parse a query string
even in a POST request.
"""

import cgi
import os

from urllib.parse import unquote_plus


class FieldStorage(cgi.FieldStorage):
    """Modified FieldStorage class for POST requests with query strings.

    Parameters in the query string which have not been sent via POST are
    appended to the field list. This is different from the behavior of
    Python versions before 2.6 which completely ignored the query string in
    POST request, but it's also different from the behavior of the later Python
    versions which append values from the query string to values sent via POST
    for parameters with the same name. With other words, our FieldStorage class
    overrides the query string parameters with the parameters sent via POST.
    """

    def __init__(self, fp=None, headers=None, outerboundary=b'',
                 environ=None, keep_blank_values=False,
                 strict_parsing=False, limit=None,
                 encoding='utf-8', errors='replace',
                 max_num_fields=None, separator='&'):
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
            if separator == '&':
                # separator is only supported since Python 3.6.13
                if max_num_fields is None:
                    # max_num_fields is only supported since Python 3.6.7
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
            else:
                super().__init__(
                    fp, headers=headers, outerboundary=outerboundary,
                    environ=environ, keep_blank_values=keep_blank_values,
                    strict_parsing=strict_parsing, limit=limit,
                    encoding=encoding, errors=errors,
                    max_num_fields=max_num_fields, separator=separator)
        finally:
            if qs_on_post:
                environ['QUERY_STRING'] = qs_on_post
        if qs_on_post:
            self.add_qs(qs_on_post)

    def add_qs(self, qs):
        """Add all non-existing parameters from the given query string."""
        # split the query string in the same way as the current Python does it
        try:
            max_num_fields = self.max_num_fields
        except AttributeError:
            # parameter did not exist before Python 3.6.7
            max_num_fields = None
        try:
            separator = self.separator
        except AttributeError:
            # splitting algorithm before Python 3.6.13
            if max_num_fields is not None:
                num_fields = 1 + qs.count('&') + qs.count(';')
                if max_num_fields < num_fields:
                    raise ValueError('Max number of fields exceeded')
            pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
        else:
            if not separator or not isinstance(separator, (str, bytes)):
                return  # invalid separator, do nothing in this case
            if max_num_fields is not None:
                num_fields = 1 + qs.count(separator)
                if max_num_fields < num_fields:
                    raise ValueError('Max number of fields exceeded')
            # new splitting algorithm that only supports one separator
            pairs = qs.split(separator)
        if not pairs:
            return  # shortcut when there are no parameters
        if self.list is None:
            # This makes sure self.keys() are available, even
            # when valid POST data wasn't encountered.
            self.list = []
        append = self.list.append
        existing_names = set(self)
        strict_parsing = self.strict_parsing
        keep_blank_values = self.keep_blank_values
        for name_value in pairs:
            nv = name_value.split('=', 1)
            if len(nv) != 2:
                if strict_parsing:
                    raise ValueError(f'bad query field: {name_value!r}')
                # Ignore parameters with no equal sign if not strict parsing
                continue
            value = unquote_plus(nv[1])
            if value or keep_blank_values:
                name = unquote_plus(nv[0])
                if name not in existing_names:
                    # Only append values that aren't already the FieldStorage;
                    # this makes POSTed vars override vars on the query string.
                    append(cgi.MiniFieldStorage(name, value))
