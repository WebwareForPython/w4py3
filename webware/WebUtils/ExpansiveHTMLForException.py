"""ExpansiveHTMLForException.py

Create expansive HTML for exceptions using the CGITraceback module.
"""

from WebUtils import CGITraceback

HTMLForExceptionOptions = {
    'table': 'background-color:#F0F0F0;font-size:10pt',
    'default': 'color:#000',
    'row.location': 'color:#009',
    'row.code': 'color:#900',
    'editlink': None,
}


def expansiveHTMLForException(context=5, options=None):
    """Create expansive HTML for exceptions."""
    if options:
        opt = HTMLForExceptionOptions.copy()
        opt.update(options)
    else:
        opt = HTMLForExceptionOptions
    return CGITraceback.html(context=context, options=opt)


# old (deprecated) alias
ExpansiveHTMLForException = expansiveHTMLForException
