import unittest

from io import StringIO

from WebUtils.HTMLTag import HTMLReader


class HTMLTagTest(unittest.TestCase):

    def setUp(self):
        self._html = """\
<html>
<head>
    <title>Example</title>
</head>
<body lang="en">
    <p>What's up, <em>doc</em>?</p>
    <hr>
    <table id="dataTable">
        <tr> <th> x </th> <th> y </th> </tr>
        <tr><td class="datum">0</td><td class="datum">0</td></tr>
    </table>
</body>
</html>"""

    def tearDown(self):
        del self._html

    def testBasics(self):
        reader = HTMLReader()
        tag = reader.readString('<html> </html>')
        self.assertEqual(tag.name(), 'html')
        self.assertEqual(reader.rootTag(), tag)
        self.assertTrue(reader.filename() is None)
        out = StringIO()
        tag.pprint(out)
        self.assertEqual(out.getvalue(), '<html>\n</html>\n')

    def testReuseReader(self):
        reader = HTMLReader()
        reader.readString('<html> </html>')
        tag = reader.readString('<html> <body> </body> </html>')
        self.assertFalse(reader.rootTag() is None)
        self.assertEqual(reader.rootTag(), tag)

        tag = reader.readString('<html> </html>', retainRootTag=0)
        self.assertFalse(tag is None)
        self.assertTrue(reader.rootTag() is None)

    def testAccess(self):
        html = HTMLReader().readString(self._html)

        # Name
        self.assertEqual(html.name(), 'html')

        # Attrs
        self.assertEqual(html.numAttrs(), 0)
        self.assertFalse(html.hasAttr('foo'))
        self.assertRaises(KeyError, html.attr, 'foo')
        self.assertTrue(html.attr('foo', None) is None)

        # Children and subtags, when both are the same.
        for numFoos, fooAt, foos in [
                [html.numChildren, html.childAt, html.children],
                [html.numSubtags, html.subtagAt, html.subtags]]:
            self.assertEqual(numFoos(), 2)
            self.assertEqual(len(foos()), 2)
            self.assertEqual(fooAt(0).name(), 'head')
            self.assertEqual(fooAt(1).name(), 'body')

        # Children and subtags when they're different
        body = html.subtagAt(1)
        p = body.subtagAt(0)
        self.assertEqual(p.name(), 'p')
        self.assertEqual(p.numChildren(), 3)
        self.assertEqual(p.numSubtags(), 1)

    def testMatchingAttr(self):
        html = HTMLReader().readString(self._html)
        self.assertEqual(
            html.tagWithMatchingAttr('lang', 'en').name(), 'body')
        self.assertEqual(
            html.tagWithMatchingAttr('id', 'dataTable').name(), 'table')
        self.assertEqual(html.tagWithId('dataTable').name(), 'table')

    def testInvalidHTML(self):
        from WebUtils.HTMLTag import (
            HTMLTagUnbalancedError, HTMLTagIncompleteError)

        reader = HTMLReader()

        html = '<html> <body> <table> </body> </html>'
        self.assertRaises(HTMLTagUnbalancedError, reader.readString, html)

        html = '<html> <body>'
        self.assertRaises(HTMLTagIncompleteError, reader.readString, html)
