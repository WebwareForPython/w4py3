import unittest

from WebUtils import Funcs


class TestFuncs(unittest.TestCase):

    def testHtmlEncode(self):
        f = Funcs.htmlEncode
        self.assertEqual(
            f('"1 < 2 & 2 > 1"'),
            '&quot;1 &lt; 2 &amp; 2 &gt; 1&quot;')
        self.assertEqual(
            f('quarks & co', (('&', 'and'),)),
            'quarks and co')
        self.assertEqual(f(None), '-')

        class Obj:
            @staticmethod
            def html():
                return 'bazong!'
        obj = Obj()
        self.assertEqual(f(obj), 'bazong!')
        obj.html = 'bazz!'
        self.assertEqual(f(obj), 'bazz!')

    def testHtmlEncodeStr(self):
        f = Funcs.htmlEncodeStr
        self.assertEqual(
            f('"1 < 2 & 2 > 1"'),
            '&quot;1 &lt; 2 &amp; 2 &gt; 1&quot;')
        self.assertEqual(
            f('quarks & co', (('&', 'and'),)),
            'quarks and co')

    def testHtmlDecode(self):
        f = Funcs.htmlDecode
        self.assertEqual(
            f('&quot;1 &lt; 2 &amp; 2 &gt; 1&quot;'),
            '"1 < 2 & 2 > 1"')
        self.assertEqual(
            f('quarks and co', (('&', 'and'),)),
            'quarks & co')

    def testHtmlRoundTrip(self):
        t = '<test>\n\t"1 < 2 & 2 > 1"\n</test>'
        self.assertEqual(Funcs.htmlDecode(Funcs.htmlEncode(t)), t)

    def testUrlEncode(self):
        f = Funcs.urlEncode
        self.assertEqual(f('"hello, world!"'), '%22hello%2C+world%21%22')

    def testUrlDecode(self):
        f = Funcs.urlDecode
        self.assertEqual(f('%22hello%2C+world%21%22'), '"hello, world!"')

    def testUrlRoundTrip(self):
        t = '<test>\n\t"50% = 50,50?"\n</test>'
        self.assertEqual(Funcs.urlDecode(Funcs.urlEncode(t)), t)

    def testHtmlDorDict(self):
        f = Funcs.htmlForDict
        self.assertEqual(
            f(dict(foo='bar', answer=42)),
            '<table class="NiceTable">\n'
            '<tr><th>answer</th><td>42</td></tr>\n'
            '<tr><th>foo</th><td>bar</td></tr>\n</table>')
        self.assertEqual(
            f(dict(foo='ba,zong', bar='ka;woom'),
              addSpace=dict(foo=',', bar=';')),
            '<table class="NiceTable">\n'
            '<tr><th>bar</th><td>ka; woom</td></tr>\n'
            '<tr><th>foo</th><td>ba, zong</td></tr>\n</table>')
        self.assertEqual(
            f(dict(foo='barbarabarbarabarbarabarbara'), maxValueLength=12),
            '<table class="NiceTable">\n'
            '<tr><th>foo</th><td>barbaraba...</td></tr>\n</table>')
        self.assertEqual(
            f(dict(foo='zing', bar='zang'),
              filterValueCallBack=lambda v, k, d: 'zung' if k == 'bar' else v),
            '<table class="NiceTable">\n'
            '<tr><th>bar</th><td>zung</td></tr>\n'
            '<tr><th>foo</th><td>zing</td></tr>\n</table>')
        self.assertEqual(
            f(dict(foo='bar'), topHeading='twinkle'),
            '<table class="NiceTable">\n'
            '<tr class="TopHeading"><th colspan="2">twinkle</th></tr>\n'
            '<tr><th>foo</th><td>bar</td></tr>\n</table>')
        self.assertEqual(
            f(dict(foo='bar'), topHeading=('key', 'value')),
            '<table class="NiceTable">\n'
            '<tr class="TopHeading"><th>key</th><th>value</th></tr>\n'
            '<tr><th>foo</th><td>bar</td></tr>\n</table>')
        self.assertEqual(
            f({'a & b': 'c & d'}),
            '<table class="NiceTable">\n'
            '<tr><th>a &amp; b</th><td>c &amp; d</td></tr>\n</table>')
        self.assertEqual(
            f({'a & b': 'c &amp; d'}, isEncoded=True),
            '<table class="NiceTable">\n'
            '<tr><th>a &amp; b</th><td>c &amp; d</td></tr>\n</table>')

    def testRequestURI(self):
        f = Funcs.requestURI
        self.assertEqual(
            f(dict(REQUEST_URI='http://w4py.org')), 'http://w4py.org')
        self.assertEqual(
            f(dict(SCRIPT_URL='http://w4py.org', QUERY_STRING='foo=bar')),
            'http://w4py.org?foo=bar')
        self.assertEqual(
            f(dict(SCRIPT_NAME='/test', QUERY_STRING='foo=bar')),
            '/test?foo=bar')

    def testNormURL(self):
        f = Funcs.normURL
        self.assertEqual(f('foo/bar'), 'foo/bar')
        self.assertEqual(f('/foo/bar'), '/foo/bar')
        self.assertEqual(f('foo/bar/'), 'foo/bar/')
        self.assertEqual(f('/foo/bar/../baz/../biz/./'), '/foo/biz/')
        self.assertEqual(f('/foo/bar/baz/biz/../../../'), '/foo/')
        self.assertEqual(f('/foo/./././././././'), '/foo/')
        self.assertEqual(f('/foo/../../../'), '/')
        self.assertEqual(f('foo///bar'), 'foo/bar')
