"""The standard web page template."""

from WebUtils import Funcs
from HTTPContent import HTTPContent


class Page(HTTPContent):
    """The standard web page template.

    Page is a type of HTTPContent that is more convenient for servlets
    which represent HTML pages generated in response to GET and POST requests.
    In fact, this is the most common type of Servlet.

    Subclasses typically override ``writeHeader``, ``writeBody`` and
    ``writeFooter``.

    They might also choose to override ``writeHTML`` entirely.

    When developing a full-blown website, it's common to create a subclass of
    ``Page`` called ``SitePage`` which defines the common look and feel of the
    website and provides site-specific convenience methods. Then all other
    pages in your application then inherit from ``SitePage``.
    """

    # region Transactions

    def defaultAction(self):
        """The default action in a Page is to writeHTML()."""
        self.writeHTML()

    # endregion Transactions

    # region Generating results

    def title(self):
        """The page title.

        Subclasses often override this method to provide a custom title.
        This title should be absent of HTML tags. This implementation
        returns the name of the class, which is sometimes appropriate
        and at least informative.
        """
        return self.__class__.__name__

    def htTitle(self):
        """The page title as HTML.

        Return self.title(). Subclasses sometimes override this to provide
        an HTML enhanced version of the title. This is the method that should
        be used when including the page title in the actual page contents.
        """
        return self.title()

    def htRootArgs(self):
        """The attributes for the <html> element.

        Returns the arguments used for the root HTML tag.
        Invoked by writeHTML() and preAction().

        Authors are encouraged to specify a lang attribute,
        giving the document's language.
        """
        return 'lang="en"'

    def htBodyArgs(self):
        """The attributes for the <body> element.

        Returns the arguments used for the HTML ``<body>`` tag.
        Invoked by writeBody().

        With the prevalence of stylesheets (CSS), you can probably skip
        this particular HTML feature, but for historical reasons this sets
        the page to black text on white.
        """
        return 'style="color:black;background-color:white"'

    def writeHTML(self):
        """Write all the HTML for the page.

        Subclasses may override this method (which is invoked by ``_respond``)
        or more commonly its constituent methods, ``writeDocType``,
        ``writeHead`` and ``writeBody``.

        You will want to override this method if:
          * you want to format the entire HTML page yourself
          * if you want to send an HTML page that has already been generated
          * if you want to use a template that generates the entire page
          * if you want to send non-HTML content; in this case, be sure to call
            self.response().setHeader('Content-Type', 'mime/type').
        """
        self.writeDocType()
        htmlArgs = self.htRootArgs()
        if htmlArgs:
            self.writeln(f'<html {htmlArgs}>')
        else:
            self.writeln('<html>')
        self.writeHead()
        self.writeBody()
        self.writeln('</html>')

    def writeDocType(self):
        """Write the DOCTYPE tag.

        Invoked by ``writeHTML`` to write the ``<!DOCTYPE ...>`` tag.

        By default this gives the HTML 5 DOCTYPE.

        Subclasses may override to specify something else.
        """
        self.writeln('<!DOCTYPE html>')

    def writeHead(self):
        """Write the <head> element of the page.

        Writes the ``<head>`` portion of the page by writing the
        ``<head>...</head>`` tags and invoking ``writeHeadParts`` in between.
        """
        wr = self.writeln
        wr('<head>')
        self.writeHeadParts()
        wr('</head>')

    def writeHeadParts(self):
        """Write the parts included in the <head> element.

        Writes the parts inside the ``<head>...</head>`` tags.
        Invokes ``writeTitle`` and then ``writeMetaData``, ``writeStyleSheet``
        and ``writeJavaScript``. Subclasses should override the ``title``
        method and the three latter methods only.
        """
        self.writeTitle()
        self.writeMetaData()
        self.writeStyleSheet()
        self.writeJavaScript()

    def writeTitle(self):
        """Write the <title> element of the page.

        Writes the ``<title>`` portion of the page.
        Uses ``title``, which is where you should override.
        """
        self.writeln(f'\t<title>{self.title()}</title>')

    def writeMetaData(self):
        """Write the meta data for the page.

        This default implementation only specifies the output encoding.
        Subclasses should override if necessary.
        """
        charset = self.outputEncoding()
        if charset:
            self.writeln(f'\t<meta charset="{charset}">')

    def writeStyleSheet(self):
        """Write the CSS for the page.

        This default implementation does nothing.
        Subclasses should override if necessary.

        A typical implementation is::

            self.writeln('<link rel="stylesheet" href="StyleSheet.css">')
        """
        # base method does nothing

    def writeJavaScript(self):
        """Write the JavaScript for the page.

        This default implementation does nothing.
        Subclasses should override if necessary.

        A typical implementation is::

            self.writeln('<script src="ajax.js"></script>')
        """
        # base method does nothing

    def writeBody(self):
        """Write the <body> element of the page.

        Writes the ``<body>`` portion of the page by writing the
        ``<body>...</body>`` (making use of ``htBodyArgs``) and
        invoking ``writeBodyParts`` in between.
        """
        wr = self.writeln
        bodyArgs = self.htBodyArgs()
        if bodyArgs:
            wr(f'<body {bodyArgs}>')
        else:
            wr('<body>')
        self.writeBodyParts()
        wr('</body>')

    def writeBodyParts(self):
        """Write the parts included in the <body> element.

        Invokes ``writeContent``. Subclasses should only override this method
        to provide additional page parts such as a header, sidebar and footer,
        that a subclass doesn't normally have to worry about writing.

        For writing page-specific content, subclasses should override
        ``writeContent`` instead. This method is intended to be overridden
        by your SitePage.

        See ``SidebarPage`` for an example override of this method.

        Invoked by ``writeBody``.
        """
        self.writeContent()

    def writeContent(self):
        """Write the unique, central content for the page.

        Subclasses should override this method (not invoking super) to write
        their unique page content.

        Invoked by ``writeBodyParts``.
        """
        self.writeln('<p>This page has not yet customized its content.</p>')

    def preAction(self, actionName):
        """Things to do before actions.

        For a page, we first writeDocType(), <html>, and then writeHead().
        """
        self.writeDocType()
        htmlArgs = self.htRootArgs()
        if htmlArgs:
            self.writeln(f'<html {htmlArgs}>')
        else:
            self.writeln('<html>')
        self.writeHead()

    def postAction(self, actionName):
        """Things to do after actions.

        Simply close the html tag (</html>).
        """
        self.writeln('</html>')

    # endregion Generating results

    # region Convenience Methods

    @staticmethod
    def htmlEncode(s):
        """HTML encode special characters.
        Alias for ``WebUtils.Funcs.htmlEncode``, quotes the special characters
        &, <, >, and \"
        """
        return Funcs.htmlEncode(s)

    @staticmethod
    def htmlDecode(s):
        """HTML decode special characters.

        Alias for ``WebUtils.Funcs.htmlDecode``. Decodes HTML entities.
        """
        return Funcs.htmlDecode(s)

    # endregion Convenience Methods
