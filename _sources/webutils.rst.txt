.. module:: WebUtils

.. _webutils:

WebUtils
========

The WebUtils package is a basic set of modules for common web related programming tasks such as encoding/decoding HTML, dealing with Cookies, etc.

See the :ref:`reference documentation <ref-webutils>` for an overview of the available functions.


HTMLForException
----------------

This module defines a function by the same name::

    def htmlForException(excInfo=None, options=None):
        ...

htmlForException returns an HTML string that presents useful information to the developer about the exception. The first argument is a tuple such as returned by ``sys.exc_info()`` which is in fact, invoked if the tuple isn't provided. The options parameter can be a dictionary to override the color options in ``HTMLForExceptionOptions`` which is currently defined as::

    HTMLForExceptionOptions = {
        'table': 'background-color:#f0f0f0',
        'default': 'color:#000',
        'row.location': 'color:#009',
        'row.code': 'color:#900',
    }


A sample HTML exception string looks like this:

.. raw:: html

    <table style="background-color:#f0f0f0:width:100%"><tr><td>
    <pre style="color:#000">Traceback (most recent call last):
    <span style="color:#009">  File "Application.py", line 90, in dispatchRequest</span>
    <span style="color:#900">    self.respond(context, response)</span>
    <span style="color:#009">  File "Application.py", line 112, in respond</span>
    <span style="color:#900">    ctx.component().respond(ctx, response)</span>
    <span style="color:#009">  File "HTTPComponent.py", line 30, in respond</span>
    <span style="color:#900">    method(ctx, response)</span>
    <span style="color:#009">  File "/home/echuck/Webware/Examples/Introspect.py", line 9, in respondToGet</span>
    <span style="color:#900">    self.write('&lt;table %s&gt;' % tableOptions)</span>
    NameError: tableOptions</pre>
    </td></tr></table>


HTTPStatusCodes
---------------

This module provides a list of well known HTTP status codes in list form and in a dictionary that can be keyed by code number or identifier.

You can index the HTTPStatusCodes dictionary by code number such as ``200``, or identifier such as ``OK``. The dictionary returned has keys ``'code'``, ``'identifier'`` and ``'htmlMsg'``. An ``'asciiMsg'`` key is provided, however, the HTML tags are not yet actually stripped out.

The ``htmlTableOfHTTPStatusCodes()`` function returns a string which is exactly that: a table containing the ``HTTPStatusCodes`` defined by the module. You can affect the formatting of the table by specifying values for the arguments. It's highly recommended that you use ``key=value`` arguments since the number and order could easily change in future versions. The definition is::

    def htmlTableOfHTTPStatusCodes(
            codes=HTTPStatusCodeList,
            tableArgs='', rowArgs='style="vertical-align:top"',
            colArgs='', headingArgs=''):
        ...

If you run the script, it will invoke ``htmlTableOfHTTPStatusCodes()`` and print its contents with some minimal HTML wrapping. You could do this::

    > cd Webware/Projects/WebUtils
    > python HTTPStatusCodes.py > HTTPStatusCodes.html

And then open the HTML file in your favorite browser.

