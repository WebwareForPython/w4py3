"""HTMLForException.py

Create HTML for exceptions.
"""

import os
import re
import sys
import traceback
import urllib.request
import urllib.parse
import urllib.error

from .Funcs import htmlEncode

HTMLForExceptionOptions = {
    'table': 'background-color:#f0f0f0',
    'default': 'color:#000',
    'row.location': 'color:#009',
    'row.code': 'color:#900',
    'editlink': None,
}

fileRE = re.compile(r'File "([^"]*)", line ([0-9]+), in ([^ ]*)')


def htmlForLines(lines, options=None):
    """Create HTML for exceptions and tracebacks from a list of strings."""

    # Set up the options:
    if options:
        opt = HTMLForExceptionOptions.copy()
        opt.update(options)
    else:
        opt = HTMLForExceptionOptions

    # Create the HTML:
    res = ['<table style="width:100%;{}">\n'.format(opt['table']),
           '<tr><td><pre style="{}">\n'.format(opt['default'])]
    for line in lines:
        match = fileRE.search(line)
        if match:
            parts = list(map(htmlEncode, line.split('\n', 2)))
            parts[0] = '<span style="{}">{}</span>'.format(
                opt['row.location'], parts[0])
            if opt['editlink']:
                parts[0] = (
                    '{} <a href="{}?filename={}&amp;line={}">'
                    '[edit]</a>'.format(
                        parts[0], opt['editlink'], urllib.parse.quote(
                            os.path.abspath(match.group(1))), match.group(2)))
            parts[1] = '<span style="{}">{}</span>'.format(
                opt['row.code'], parts[1])
            line = '\n'.join(parts)
            res.append(line)
        else:
            res.append(htmlEncode(line))
    if lines:
        if res[-1][-1] == '\n':
            res[-1] = res[-1].rstrip()
    res.extend(['</pre></td></tr>\n', '</table>\n'])
    return ''.join(res)


def htmlForStackTrace(frame=None, options=None):
    """Get HTML for displaying a stack trace.

    Returns an HTML string that presents useful information to the developer
    about the stack. The first argument is a stack frame such as returned by
    sys._getframe() which is in fact invoked if a stack frame isn't provided.
    """

    # Get the stack frame if needed:
    if frame is None:
        frame = sys._getframe()

    # Return formatted stack traceback
    return htmlForLines(traceback.format_stack(frame), options)


def htmlForException(excInfo=None, options=None):
    """Get HTML for displaying an exception.

    Returns an HTML string that presents useful information to the developer
    about the exception. The first argument is a tuple such as returned by
    sys.exc_info() which is in fact invoked if the tuple isn't provided.
    """

    # Get the excInfo if needed:
    if excInfo is None:
        excInfo = sys.exc_info()

    # Return formatted exception traceback
    return htmlForLines(traceback.format_exception(*excInfo), options)


# old (deprecated) aliases
HTMLForLines, HTMLForStackTrace, HTMLForException = (
    htmlForLines, htmlForStackTrace, htmlForException)
