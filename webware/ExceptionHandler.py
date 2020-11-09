"""Exception handling."""

import os
import sys
import poplib
import smtplib
import traceback
from io import StringIO
from random import randint
from time import time, localtime

from email.message import Message
from email.utils import formatdate

from MiscUtils.Funcs import asclocaltime
from WebUtils.HTMLForException import htmlForException
from WebUtils.Funcs import htmlForDict, htmlEncode


class Singleton:
    """A singleton object."""


class ExceptionHandler:
    """Exception handling.

    ExceptionHandler is a utility class for Application that is created
    to handle a particular exception. The object is a one-shot deal.
    After handling an exception, it should be removed.

    At some point, the exception handler sends `writeExceptionReport` to the
    transaction (if present), which in turn sends it to the other transactional
    objects (application, request, response, etc.)  The handler is the single
    argument for this message.

    Classes may find it useful to do things like this::

        exceptionReportAttrs = ['foo', 'bar', 'baz']
        def writeExceptionReport(self, handler):
            handler.writeTitle(self.__class__.__name__)
            handler.writeAttrs(self, self.exceptionReportAttrs)

    The handler write methods that may be useful are:

      * write
      * writeTitle
      * writeDict
      * writeAttrs

    Derived classes must not assume that the error occurred in a
    transaction.  self._tra may be None for exceptions outside
    of transactions.

    **HOW TO CREATE A CUSTOM EXCEPTION HANDLER**

    In the ``__init__.py`` of your context::

        from ExceptionHandler import ExceptionHandler as _ExceptionHandler

        class ExceptionHandler(_ExceptionHandler):

            _hideValuesForFields = _ExceptionHandler._hideValuesForFields + [
                'foo', 'bar']

            def work(self):
                _ExceptionHandler.work(self)
                # do whatever
                # override other methods if you like

        def contextInitialize(app, ctxPath):
            app._exceptionHandlerClass = ExceptionHandler

    You can also control the errors with settings in ``Application.config``.
    """
    # keep these lower case to support case insensitivity:
    _hideValuesForFields = [
        'password', 'passwd', 'pwd',
        'creditcard', 'credit card', 'cc', 'pin', 'tan']
    _hiddenString = '*** hidden ***'
    _addSpace = {
        'PATH': os.pathsep, 'CLASSPATH': os.pathsep,
        'HTTP_ACCEPT': ',', 'HTTP_ACCEPT_CHARSET': ',',
        'HTTP_ACCEPT_ENCODING': ',', 'HTTP_ACCEPT_LANGUAGE': ','}
    _docType = '<!DOCTYPE html>'
    _emailBody = (
        'Webware caught an exception while processing'
        ' a request for "{path}" at {ascTime} (timestamp: {time}).'
        ' The plain text traceback from Python is printed below and'
        ' the full HTML error report from Webware is attached.\n\n')

    # region Init

    def __init__(
            self, application, transaction, excInfo, formatOptions=None):
        """Create an exception handler instance.

        ExceptionHandler instances are created anew for each exception.
        Instantiating ExceptionHandler completes the process --
        the caller need not do anything else.
        """
        # Keep references to the objects
        self._app = application
        self._tra = transaction
        self._exc = excInfo
        if self._tra:
            self._req = self._tra.request()
            self._res = self._tra.response()
        else:
            self._req = self._res = None

        self._formatOptions = formatOptions

        # Make some repairs, if needed. We use the transaction
        # and response to get the error page back out.

        # Cache MaxValueLengthInExceptionReport for speed
        self._maxValueLength = self.setting('MaxValueLengthInExceptionReport')

        # exception occurrence time (overridden by response.endTime())
        self._time = time()

        # Get to work
        self.work()

    # endregion Init

    # region Accessors

    def setting(self, name):
        """Settings are inherited from Application."""
        return self._app.setting(name)

    def servletPathname(self):
        """The full filesystem path for the servlet."""
        try:
            return self._tra.request().serverSidePath()
        except Exception:
            return None

    def basicServletName(self):
        """The base name for the servlet (sans directory)."""
        name = self.servletPathname()
        if name is None:
            return 'unknown'
        return os.path.basename(name)

    # endregion Accessors

    # region Exception Handling

    def work(self):
        """Main error handling method.

        Invoked by ``__init__`` to do the main work. This calls
        `logExceptionToConsole`, then checks settings to see if it should call
        `saveErrorPage` (to save the error to disk) and `emailException`.

        It also sends gives a page from `privateErrorPage` or
        `publicErrorPage` (which one based on `ShowDebugInfoOnErrors`).
        """
        if self._res:
            self._res.recordEndTime()
            self._time = self._res.endTime()

        self.logExceptionToConsole()

        # Write the error page out to the response if available:
        if self._res and (
                not self._res.isCommitted() or
                self._res.header('Content-Type', None) == 'text/html'):
            if not self._res.isCommitted():
                self._res.reset()
                self._res.setStatus(500, "Servlet Error")
            if self.setting('ShowDebugInfoOnErrors') == 1:
                publicErrorPage = self.privateErrorPage()
            else:
                publicErrorPage = self.publicErrorPage()
            self._res.write(publicErrorPage)

            # Add a large block comment; this prevents IE from overriding the
            # page with its own generic error 500 page
            self._res.write(
                '<!-- - - - - - - - - - - - - - - - - - -->\n' * 100)

        privateErrorPage = None
        if self.setting('SaveErrorMessages'):
            privateErrorPage = self.privateErrorPage()
            filename = self.saveErrorPage(privateErrorPage)
        else:
            filename = None

        self.logExceptionToDisk(errorMsgFilename=filename)

        if self.setting('EmailErrors'):
            if privateErrorPage is None:
                privateErrorPage = self.privateErrorPage()
            try:
                self.emailException(privateErrorPage)
            except Exception as e:
                print("Could not send error email:", e)

    def logExceptionToConsole(self, stderr=None):
        """Log an exception.

        Logs the time, servlet name and traceback to the console
        (typically stderr). This usually results in the information
        appearing in console/terminal from which the Application was launched.
        """
        if stderr is None:
            stderr = sys.stderr
        stderr.write(
            f'[{asclocaltime(self._time)}] [error] Webware:'
            f' Error while executing script {self.servletPathname()}\n')
        traceback.print_exc(file=stderr)

    def publicErrorPage(self):
        """Return a public error page.

        Returns a brief error page telling the user that an error has occurred.
        Body of the message comes from ``UserErrorMessage`` setting.
        """
        return '\n'.join((
            docType(), '<html>', '<head>',
            '<title>Error</title>', htStyle(), '</head>',
            '<body style="color:black;background-color:white">',
            htTitle('Error'),
            '<p>{}</p>'.format(self.setting('UserErrorMessage')),
            '</body>', '</html>\n'))

    def privateErrorPage(self):
        """Return a private error page.

        Returns an HTML page intended for the developer with
        useful information such as the traceback.

        Most of the contents are generated in `htmlDebugInfo`.
        """
        return '\n'.join((
            docType(), '<html>', '<head>',
            '<title>Error</title>', htStyle(), '</head>',
            '<body style="color:black;background-color:white">',
            htTitle('Error'),
            '<p>{}</p>'.format(self.setting('UserErrorMessage')),
            self.htmlDebugInfo(), '</body>', '</html>\n'))

    def htmlDebugInfo(self):
        """Return the debug info.

        Return HTML-formatted debugging information on the current exception.
        Calls `writeHTML`, which uses ``self.write(...)`` to add content.
        """
        self._html = []
        self.writeHTML()
        html = ''.join(self._html)
        self._html = None
        return html

    def writeHTML(self):
        """Write the traceback.

        Writes all the parts of the traceback, invoking:
          * `writeTraceback`
          * `writeMiscInfo`
          * `writeTransaction`
          * `writeEnvironment`
          * `writeIds`
          * `writeFancyTraceback`
        """
        self.writeTraceback()
        self.writeMiscInfo()
        self.writeTransaction()
        self.writeEnvironment()
        self.writeIds()
        self.writeFancyTraceback()

    # endregion Exception Handling

    # region Write Methods

    def write(self, s):
        """Output `s` to the body."""
        self._html.append(str(s))

    def writeln(self, s):
        """Output `s` plus a newline."""
        self._html.append(str(s))
        self._html.append('\n')

    def writeTitle(self, s):
        """Output the sub-heading to define a section."""
        self.writeln(htTitle(s))

    def writeDict(self, d, heading=None, encoded=None):
        """Output a table-formatted dictionary."""
        self.writeln(htmlForDict(
            d, addSpace=self._addSpace,
            filterValueCallBack=self.filterDictValue,
            maxValueLength=self._maxValueLength,
            topHeading=heading, isEncoded=encoded))

    def writeAttrs(self, obj, attrNames):
        """Output object attributes.

        Writes the attributes of the object as given by attrNames.
        Tries ``obj._name`` first, followed by ``obj.name()``.
        Is resilient regarding exceptions so as not to spoil the
        exception report.
        """
        attrs = {}
        for name in attrNames:
            value = getattr(obj, '_' + name, Singleton)  # go for attribute
            try:
                if value is Singleton:
                    value = getattr(obj, name, Singleton)  # go for method
                    if value is Singleton:
                        value = '(could not find attribute or method)'
                    else:
                        try:
                            if callable(value):
                                value = value()
                            value = self.repr(value)
                        except Exception as e:
                            value = (
                                '(exception during method call:'
                                f' {e.__class__.__name__}: {e})')
                else:
                    value = self.repr(value)
            except Exception as e:
                value = (
                    '(exception during value processing:'
                    f' {e.__class__.__name__}: {e})')
            attrs[name] = value
        self.writeDict(attrs, ('Attribute', 'Value'), True)

    # endregion Write Methods

    # region Traceback sections

    def writeTraceback(self):
        """Output the traceback.

        Writes the traceback, with most of the work done
        by `WebUtils.HTMLForException.htmlForException`.
        """
        self.writeTitle('Traceback')
        self.write(f'<p><em>{self.servletPathname()}</em></p>')
        self.write(htmlForException(self._exc, self._formatOptions))

    def writeMiscInfo(self):
        """Output misc info.

        Write a couple little pieces of information about the environment.
        """
        self.writeTitle('MiscInfo')
        info = {
            'time': asclocaltime(self._time),
            'filename': self.servletPathname(),
            'os.getcwd()': os.getcwd(),
            'sys.path': sys.path,
            'sys.version': sys.version,
        }
        self.writeDict(info)

    def writeTransaction(self):
        """Output transaction.

        Lets the transaction talk about itself, using
        `Transaction.writeExceptionReport`.
        """
        if self._tra:
            self._tra.writeExceptionReport(self)
        else:
            self.writeTitle("No current Transaction.")

    def writeEnvironment(self):
        """Output environment.

        Writes the environment this is being run in. This is *not* the
        environment that was passed in with the request (holding the CGI
        information) -- it's just the information from the environment
        that the Application is being executed in.
        """
        self.writeTitle('Environment')
        self.writeDict(os.environ)

    def writeIds(self):
        """Output OS identification.

        Prints some values from the OS (like processor ID).
        """
        self.writeTitle('OS Ids')
        self.writeDict(osIdDict(), ('Name', 'Value'))

    def writeFancyTraceback(self):
        """Output a fancy traceback, using CGITraceback."""
        if self.setting('IncludeFancyTraceback'):
            self.writeTitle('Fancy Traceback')
            try:
                from WebUtils.ExpansiveHTMLForException import (
                    expansiveHTMLForException)
                self.write(expansiveHTMLForException(
                    context=self.setting('FancyTracebackContext')))
            except Exception:
                self.write(
                    '<p>Unable to generate a fancy traceback'
                    ' (uncaught exception)!</p>')
                try:
                    self.write(htmlForException(sys.exc_info()))
                except Exception:
                    self.write(
                        '<p>Unable to even generate a normal traceback'
                        ' of the exception in fancy traceback!</p>')

    def saveErrorPage(self, html):
        """Save the error page.

        Saves the given HTML error page for later viewing by
        the developer, and returns the filename used.
        """
        filename = os.path.join(
            self._app._errorMessagesDir, self.errorPageFilename())
        try:
            with open(filename, 'w') as f:
                f.write(html)
        except IOError:
            sys.stderr.write(
                f'[{asclocaltime(self._time)}] [error] Webware:'
                f' Cannot save error page ({filename})\n')
        else:
            return filename

    def errorPageFilename(self):
        """Create filename for error page.

        Construct a filename for an HTML error page, not including the
        ``ErrorMessagesDir`` setting (which `saveError` adds on).
        """
        # Note: Using the timestamp and a random number is a poor technique
        # for filename uniqueness, but it is fast and good enough in practice.
        name = self.basicServletName()
        ts = '{:4d}-{:02d}-{:02d}-{:02d}-{:02d}-{:02d}'.format(
            *localtime(self._time)[:6])
        rnd = randint(0, 999999)
        return f'Error-{name}-{ts}-{rnd:06d}.html'

    def logExceptionToDisk(self, errorMsgFilename=None):
        """Log the exception to disk.

        Writes a tuple containing (date-time, filename, pathname,
        exception-name, exception-data, error report filename)
        to the errors file (typically 'Errors.csv') in CSV format.
        Invoked by `handleException`.
        """
        if not self.setting('LogErrors'):
            return
        err, msg = self._exc[:2]
        err, msg = err.__name__, str(msg)

        logLine = (
            asclocaltime(self._time),
            self.basicServletName(), self.servletPathname(),
            err, msg, errorMsgFilename or '')

        def fixElement(element):
            element = str(element)
            if ',' in element or '"' in element:
                element = element.replace('"', '""')
                element = f'"{element}"'
            return element

        logLine = ','.join(map(fixElement, logLine)) + '\n'
        filename = self._app.setting('ErrorLogFilename')
        try:
            if os.path.exists(filename):
                with open(filename, 'a') as f:
                    f.write(logLine)
            else:
                with open(filename, 'w') as f:
                    f.write(
                        'time,filename,pathname,exception name,'
                        'exception data,error report filename\n')
                    f.write(logLine)
        except Exception as e:
            print('Could not write to error log:', e)

    def emailException(self, htmlErrMsg):
        """Email the exception.

        Send the exception via mail, either as an attachment,
        or as the body of the mail.
        """
        message = Message()

        # Construct the message headers
        headers = self.setting('ErrorEmailHeaders').copy()
        headers['Date'] = formatdate()
        headers['Mime-Version'] = '1.0'
        headers['Subject'] = '{} {}: {}'.format(
            headers.get('Subject', '[Webware Error]'), *sys.exc_info()[:2])
        for header, value in headers.items():
            if isinstance(value, (list, tuple)):
                value = ','.join(value)
            message.add_header(header, value)

        # Construct the message body
        if self.setting('EmailErrorReportAsAttachment'):
            # start off with a text/plain part
            text = self._emailBody.format(
                path=self.servletPathname(),
                ascTime=asclocaltime(self._time), time=self._time)
            message.set_type('multipart/mixed')
            part = Message()
            part.set_type('text/plain')
            body = StringIO()
            body.write(text)
            traceback.print_exc(file=body)
            part.set_payload(body.getvalue())
            body.close()
            message.attach(part)
            part = Message()
            # now add htmlErrMsg
            part.add_header('Content-Transfer-Encoding', '7bit')
            part.add_header(
                'Content-Description',
                'HTML version of Webware error message')
            part.add_header(
                'Content-Disposition',
                'attachment', filename='WebwareErrorMsg.html')
            part.set_type('text/html')
            part.set_payload(htmlErrMsg)
            message.attach(part)
        else:
            message.set_type('text/html')
            message.set_payload(htmlErrMsg, 'us-ascii')

        # Send the message
        server = self.setting('ErrorEmailServer')
        # This setting can be: server, server:port, server:port:user:password
        # or server:port:user:password:popserver:popport for "smtp after pop".
        parts = server.split(':', 5)
        server = port = user = passwd = None
        popserver = popssl = popport = None
        try:
            # fetch individual parts until we get an IndexError
            server = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                pass
            user = parts[2]
            passwd = parts[3]
            popserver = parts[4]
            try:
                popport = int(parts[5])
            except ValueError:
                popport = None
            if parts[6].lower() == 'ssl':
                popssl = True
        except IndexError:
            pass
        if user and passwd and popserver:
            # SMTP after POP
            if popssl is None and popport == 995:
                popssl = True
            popssl = poplib.POP3_SSL if popssl else poplib.POP3
            if popport:
                popserver = popssl(popserver, popport)
            else:
                popserver = popssl(popserver)
            popserver.set_debuglevel(0)
            popserver.user(user)
            popserver.pass_(passwd)
            try:
                popserver.quit()
            except Exception:
                pass
        if port:
            server = smtplib.SMTP(server, port)
        else:
            server = smtplib.SMTP(server)
        try:
            server.set_debuglevel(0)
            if user and passwd and not popserver:
                # SMTP-AUTH
                server.ehlo()
                if server.has_extn('starttls'):
                    server.starttls()
                    server.ehlo()
                server.login(user, passwd)
            body = message.as_string()
            server.sendmail(headers['From'], headers['To'], body)
        finally:
            try:
                server.quit()
            except Exception:
                pass

    # endregion Traceback sections

    # region Filtering

    def filterDictValue(self, value, key, _dict):
        """Filter dictionary values.

        Filters keys from a dict.  Currently ignores the
        dictionary, and just filters based on the key.
        """
        return self.filterValue(value, key)

    def filterValue(self, value, key):
        """Filter values.

        This is the core filter method that is used in all filtering.
        By default, it simply returns self._hiddenString if the key is
        in self._hideValuesForField (case insensitive). Subclasses
        could override for more elaborate filtering techniques.
        """
        try:
            key = key.lower()
        except Exception:
            pass
        if key in self._hideValuesForFields:
            return self._hiddenString
        return value

    # endregion Filtering

    # region Utility

    def repr(self, value):
        """Get HTML encoded representation.

        Returns the repr() of value already HTML encoded. As a special case,
        dictionaries are nicely formatted in table.

        This is a utility method for `writeAttrs`.
        """
        if isinstance(value, dict):
            return htmlForDict(
                value, addSpace=self._addSpace,
                filterValueCallBack=self.filterDictValue,
                maxValueLength=self._maxValueLength)
        rep = repr(value)
        if self._maxValueLength and len(rep) > self._maxValueLength:
            rep = rep[:self._maxValueLength] + '...'
        return htmlEncode(rep)

    # endregion Utility


# region Misc functions

def docType():
    """Return the document type for the page."""
    return '<!DOCTYPE html>'


def htStyle():
    """Return the page style."""
    return '''<style>
body {
    background-color: white;
    color: #080810;
    font-size: 11pt;
    font-family: Tahoma,Verdana,Arial,Helvetica,sans-serif;
    margin: 0;
    padding: 8pt;
}
h2.section {
    font-size: 14pt;
    background-color:#933;
    color:white;
    text-align:center;
}
table.NiceTable {
    font-size: 10pt;
}
table.NiceTable td {
    background-color: #eee;
    color: #111;
}
table.NiceTable th {
    background-color: #bbb;
    color: black;
    text-align: left;
}
table.NiceTable tr.TopHeading th {
    background-color: #555;
    color: white;
    text-align: center;
}
table.NiceTable table.NiceTable td {
    background-color: #ddd;
    color: #222;
}
table.NiceTable table.NiceTable th {
    background-color: #ccc;
    color: black;
    font-weight: normal;
}
</style>'''


def htTitle(name):
    """Format a `name` as a section title."""
    return f'<h2 class="section">{name}</h2>'


def osIdDict():
    """Get all OS id information.

    Returns a dictionary containing id information such as pid and uid.
    """
    ids = ('egid', 'euid', 'gid', 'groups', 'pgrp', 'pid', 'ppid', 'uid')
    attrs = {}
    for id_ in ids:
        try:
            value = getattr(os, 'get' + id_)()
        except AttributeError:
            pass
        else:
            attrs[id_] = value
    return attrs

# endregion Misc functions
