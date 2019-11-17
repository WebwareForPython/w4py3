from os import sep

from .ExamplePage import ExamplePage


class View(ExamplePage):
    """View the source of a Webware servlet.

    For each Webware example, you will see a sidebar with various menu items,
    one of which is "View source of <em>example</em>". This link points to the
    View servlet and passes the filename of the current servlet. The View
    servlet then loads that file's source code and displays it in the browser
    for your viewing pleasure.

    Note that if the View servlet isn't passed a filename,
    it prints the View's docstring which you are reading right now.
    """

    def writeContent(self):
        req = self.request()
        if req.hasField('filename'):
            trans = self.transaction()
            filename = req.field('filename')
            if sep in filename:
                self.write(
                    '<h3 style="color:red">Error</h3>'
                    '<p>Cannot request a file'
                    ' outside of this directory {filename!r}</p>')
                return
            filename = self.request().serverSidePath(filename)
            self.request().fields()['filename'] = filename
            trans.application().forward(trans, 'Colorize.py')
        else:
            doc = self.__class__.__doc__.split('\n', 1)
            doc[1] = '</p>\n<p>'.join(doc[1].split('\n\n'))
            self.writeln('<h2>{}</h2>\n<p>{}</p>'.format(*doc))
