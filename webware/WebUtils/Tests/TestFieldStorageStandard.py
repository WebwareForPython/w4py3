"""Test standard functionality of FieldStorage."""

import sys
import tempfile
import unittest
from collections import namedtuple
from io import BytesIO

import WebUtils.FieldStorage as cgi


class HackedSysModule:
    argv = []
    stdin = sys.stdin


cgi.sys = HackedSysModule()


def genResult(data, environ):
    encoding = 'latin-1'
    fakeStdin = BytesIO(data.encode(encoding))
    fakeStdin.seek(0)
    form = cgi.FieldStorage(fp=fakeStdin, environ=environ, encoding=encoding)

    return {k: form.getlist(k) if isinstance(v, list) else v.value
            for k, v in dict(form).items()}


class CgiTests(unittest.TestCase):

    def testFieldStorageProperties(self):
        fs = cgi.FieldStorage()
        self.assertFalse(fs)
        self.assertIn("FieldStorage", repr(fs))
        self.assertEqual(list(fs), list(fs.keys()))
        fs.list.append(namedtuple('MockFieldStorage', 'name')('fieldvalue'))
        self.assertTrue(fs)

    def testFieldStorageInvalid(self):
        self.assertRaises(TypeError, cgi.FieldStorage, "not-a-file-obj",
                          environ={"REQUEST_METHOD": "PUT"})
        self.assertRaises(TypeError, cgi.FieldStorage, "foo", "bar")
        fs = cgi.FieldStorage(headers={'content-type': 'text/plain'})
        self.assertRaises(TypeError, bool, fs)

    def testSeparator(self):
        parseSemicolon = [
            ("x=1;y=2.0", {'x': ['1'], 'y': ['2.0']}),
            ("x=1;y=2.0;z=2-3.%2b0",
             {'x': ['1'], 'y': ['2.0'], 'z': ['2-3.+0']}),
            (";", ValueError("bad query field: ''")),
            (";;", ValueError("bad query field: ''")),
            ("=;a", ValueError("bad query field: 'a'")),
            (";b=a", ValueError("bad query field: ''")),
            ("b;=a", ValueError("bad query field: 'b'")),
            ("a=a+b;b=b+c", {'a': ['a b'], 'b': ['b c']}),
            ("a=a+b;a=b+a", {'a': ['a b', 'b a']}),
        ]
        for orig, expect in parseSemicolon:
            env = {'QUERY_STRING': orig}
            fs = cgi.FieldStorage(separator=';', environ=env)
            if isinstance(expect, dict):
                for key in expect:
                    expectValue = expect[key]
                    self.assertIn(key, fs)
                    value = fs.getvalue(key)
                    if len(expectValue) > 1:
                        self.assertEqual(value, expectValue)
                    else:
                        self.assertEqual(value, expectValue[0])

    def testFieldStorageReadline(self):
        class TestReadlineFile:
            def __init__(self, file):
                self.file = file
                self.numCalls = 0

            def readline(self, size=None):
                self.numCalls += 1
                if size:
                    return self.file.readline(size)
                return self.file.readline()

            def __getattr__(self, name):
                file = self.__dict__['file']
                attr = getattr(file, name)
                if not isinstance(attr, int):
                    setattr(self, name, attr)
                return attr

        f = TestReadlineFile(tempfile.TemporaryFile("wb+"))
        self.addCleanup(f.close)
        f.write(b'x' * 256 * 1024)
        f.seek(0)
        env = {'REQUEST_METHOD': 'PUT'}
        fs = cgi.FieldStorage(fp=f, environ=env)
        self.addCleanup(fs.file.close)
        self.assertGreater(f.numCalls, 2)
        f.close()

    def testFieldStorageMultipart(self):
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE':
                'multipart/form-data; boundary={}'.format(BOUNDARY),
            'CONTENT_LENGTH': '558'}
        fp = BytesIO(POSTDATA.encode('latin-1'))
        fs = cgi.FieldStorage(fp, environ=env, encoding="latin-1")
        self.assertEqual(len(fs.list), 4)
        expect = [{'name': 'id', 'filename': None, 'value': '1234'},
                  {'name': 'title', 'filename': None, 'value': ''},
                  {'name': 'file', 'filename': 'test.txt',
                   'value': b'Testing 123.\n'},
                  {'name': 'submit', 'filename': None, 'value': ' Add '}]
        for i, f in enumerate(fs.list):
            for k, exp in expect[i].items():
                got = getattr(f, k)
                self.assertEqual(got, exp)

    def testFieldStorageMultipartLeadingWhitespace(self):
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE':
                'multipart/form-data; boundary={}'.format(BOUNDARY),
            'CONTENT_LENGTH': '560'}
        fp = BytesIO(b"\r\n" + POSTDATA.encode('latin-1'))
        fs = cgi.FieldStorage(fp, environ=env, encoding="latin-1")
        self.assertEqual(len(fs.list), 4)
        expect = [{'name': 'id', 'filename': None, 'value': '1234'},
                  {'name': 'title', 'filename': None, 'value': ''},
                  {'name': 'file', 'filename': 'test.txt',
                   'value': b'Testing 123.\n'},
                  {'name': 'submit', 'filename': None, 'value': ' Add '}]
        for i, f in enumerate(fs.list):
            for k, exp in expect[i].items():
                got = getattr(f, k)
                self.assertEqual(got, exp)

    def testFieldStorageMultipartNonAscii(self):
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE':
                'multipart/form-data; boundary={}'.format(BOUNDARY),
            'CONTENT_LENGTH': '558'}
        for encoding in ('iso-8859-1', 'utf-8'):
            fp = BytesIO(POSTDATA_NON_ASC.encode(encoding))
            fs = cgi.FieldStorage(fp, environ=env, encoding=encoding)
            self.assertEqual(len(fs.list), 1)
            expect = [
                {'name': 'id', 'filename': None, 'value': '\xe7\xf1\x80'}]
            for i, f in enumerate(fs.list):
                for k, exp in expect[i].items():
                    got = getattr(f, k)
                    self.assertEqual(got, exp)

    def testFieldStorageMultipartMaxline(self):
        maxline = 1 << 16
        self.maxDiff = None

        def check(content):
            data = """---123
Content-Disposition: form-data; name="upload"; filename="fake.txt"
Content-Type: text/plain

%s
---123--
""".replace('\n', '\r\n') % content
            environ = {
                'CONTENT_LENGTH':   str(len(data)),
                'CONTENT_TYPE':     'multipart/form-data; boundary=-123',
                'REQUEST_METHOD':   'POST',
            }
            self.assertEqual(genResult(data, environ),
                             {'upload': content.encode('latin1')})
        check('x' * (maxline - 1))
        check('x' * (maxline - 1) + '\r')
        check('x' * (maxline - 1) + '\r' + 'y' * (maxline - 1))

    def testFieldStorageMultipartW3c(self):
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE':
                'multipart/form-data; boundary={}'.format(BOUNDARY_W3),
            'CONTENT_LENGTH': str(len(POSTDATA_W3))}
        fp = BytesIO(POSTDATA_W3.encode('latin-1'))
        fs = cgi.FieldStorage(fp, environ=env, encoding="latin-1")
        self.assertEqual(len(fs.list), 2)
        self.assertEqual(fs.list[0].name, 'submit-name')
        self.assertEqual(fs.list[0].value, 'Larry')
        self.assertEqual(fs.list[1].name, 'files')
        files = fs.list[1].value
        self.assertEqual(len(files), 2)
        expect = [{'name': None, 'filename': 'file1.txt',
                   'value': b'... contents of file1.txt ...'},
                  {'name': None, 'filename': 'file2.gif',
                   'value': b'...contents of file2.gif...'}]
        for i, f in enumerate(files):
            for k, exp in expect[i].items():
                got = getattr(f, k)
                self.assertEqual(got, exp)

    def testFieldStoragePartContentLength(self):
        boundary = "JfISa01"
        postData = """--JfISa01
Content-Disposition: form-data; name="submit-name"
Content-Length: 5

Larry
--JfISa01"""
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE':
                'multipart/form-data; boundary={}'.format(boundary),
            'CONTENT_LENGTH': str(len(postData))}
        fp = BytesIO(postData.encode('latin-1'))
        fs = cgi.FieldStorage(fp, environ=env, encoding="latin-1")
        self.assertEqual(len(fs.list), 1)
        self.assertEqual(fs.list[0].name, 'submit-name')
        self.assertEqual(fs.list[0].value, 'Larry')

    def testFieldStorageMultipartNoContentLength(self):
        fp = BytesIO(b"""--MyBoundary
Content-Disposition: form-data; name="my-arg"; filename="foo"

Test

--MyBoundary--
""")
        env = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "multipart/form-data; boundary=MyBoundary",
            "wsgi.input": fp,
        }
        fields = cgi.FieldStorage(fp, environ=env)

        self.assertEqual(len(fields["my-arg"].file.read()), 5)

    def testFieldStorageAsContextManager(self):
        fp = BytesIO(b'x' * 10)
        env = {'REQUEST_METHOD': 'PUT'}
        with cgi.FieldStorage(fp=fp, environ=env) as fs:
            content = fs.file.read()
            self.assertFalse(fs.file.closed)
        self.assertTrue(fs.file.closed)
        self.assertEqual(content, 'x' * 10)
        with self.assertRaisesRegex(
                ValueError, 'I/O operation on closed file'):
            fs.file.read()

    _qsResult = {
        'key1': 'value1',
        'key2': ['value2x', 'value2y'],
        'key3': 'value3',
        'key4': 'value4'
    }

    _qsResultModified = {
        'key1': 'value1',
        'key2': 'value2x',
        'key3': 'value3',
        'key4': 'value4'
    }

    def testQSAndUrlEncode(self):
        data = "key2=value2x&key3=value3&key4=value4"
        environ = {
            'CONTENT_LENGTH':   str(len(data)),
            'CONTENT_TYPE':     'application/x-www-form-urlencoded',
            'QUERY_STRING':     'key1=value1&key2=value2y',
            'REQUEST_METHOD':   'POST',
        }
        v = genResult(data, environ)
        self.assertNotEqual(self._qsResult, v)
        self.assertEqual(self._qsResultModified, v)

    def testMaxNumFields(self):
        data = '&'.join(['a=a']*11)
        environ = {
            'CONTENT_LENGTH': str(len(data)),
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'REQUEST_METHOD': 'POST',
        }

        with self.assertRaises(ValueError):
            cgi.FieldStorage(
                fp=BytesIO(data.encode()),
                environ=environ,
                max_num_fields=10,
            )

        data = """---123
Content-Disposition: form-data; name="a"

3
---123
Content-Type: application/x-www-form-urlencoded

a=4
---123
Content-Type: application/x-www-form-urlencoded

a=5
---123--
"""
        environ = {
            'CONTENT_LENGTH':   str(len(data)),
            'CONTENT_TYPE':     'multipart/form-data; boundary=-123',
            'QUERY_STRING':     'a=1&a=2',
            'REQUEST_METHOD':   'POST',
        }

        with self.assertRaises(ValueError):
            cgi.FieldStorage(
                fp=BytesIO(data.encode()),
                environ=environ,
                max_num_fields=4,
            )
        cgi.FieldStorage(
            fp=BytesIO(data.encode()),
            environ=environ,
            max_num_fields=5,
        )

    def testQSAndFormData(self):
        data = """---123
Content-Disposition: form-data; name="key2"

value2y
---123
Content-Disposition: form-data; name="key3"

value3
---123
Content-Disposition: form-data; name="key4"

value4
---123--
"""
        environ = {
            'CONTENT_LENGTH':   str(len(data)),
            'CONTENT_TYPE':     'multipart/form-data; boundary=-123',
            'QUERY_STRING':     'key1=value1&key2=value2x',
            'REQUEST_METHOD':   'POST',
        }
        v = genResult(data, environ)
        self.assertEqual(self._qsResult, v)

    def testQSAndFormDataFile(self):
        data = """---123
Content-Disposition: form-data; name="key2"

value2y
---123
Content-Disposition: form-data; name="key3"

value3
---123
Content-Disposition: form-data; name="key4"

value4
---123
Content-Disposition: form-data; name="upload"; filename="fake.txt"
Content-Type: text/plain

this is the content of the fake file

---123--
"""
        environ = {
            'CONTENT_LENGTH':   str(len(data)),
            'CONTENT_TYPE':     'multipart/form-data; boundary=-123',
            'QUERY_STRING':     'key1=value1&key2=value2x',
            'REQUEST_METHOD':   'POST',
        }
        result = self._qsResult.copy()
        result['upload'] = b'this is the content of the fake file\n'
        v = genResult(data, environ)
        self.assertEqual(result, v)

    def testParseHeader(self):
        parseHeader = cgi.parse_header
        self.assertEqual(
            parseHeader("text/plain"),
            ("text/plain", {}))
        self.assertEqual(
            parseHeader("text/vnd.just.made.this.up ; "),
            ("text/vnd.just.made.this.up", {}))
        self.assertEqual(
            parseHeader("text/plain;charset=us-ascii"),
            ("text/plain", {"charset": "us-ascii"}))
        self.assertEqual(
            parseHeader('text/plain ; charset="us-ascii"'),
            ("text/plain", {"charset": "us-ascii"}))
        self.assertEqual(
            parseHeader('text/plain ; charset="us-ascii"; another=opt'),
            ("text/plain", {"charset": "us-ascii", "another": "opt"}))
        self.assertEqual(
            parseHeader('attachment; filename="silly.txt"'),
            ("attachment", {"filename": "silly.txt"}))
        self.assertEqual(
            parseHeader('attachment; filename="strange;name"'),
            ("attachment", {"filename": "strange;name"}))
        self.assertEqual(
            parseHeader('attachment; filename="strange;name";size=123;'),
            ("attachment", {"filename": "strange;name", "size": "123"}))
        self.assertEqual(
            parseHeader('form-data; name="files"; filename="fo\\"o;bar"'),
            ("form-data", {"name": "files", "filename": 'fo"o;bar'}))


BOUNDARY = "---------------------------721837373350705526688164684"

POSTDATA = """-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="id"

1234
-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="title"


-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="file"; filename="test.txt"
Content-Type: text/plain

Testing 123.

-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="submit"

 Add\x20
-----------------------------721837373350705526688164684--
"""

POSTDATA_NON_ASC = """-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="id"

\xe7\xf1\x80
-----------------------------721837373350705526688164684
"""

BOUNDARY_W3 = "AaB03x"
POSTDATA_W3 = """--AaB03x
Content-Disposition: form-data; name="submit-name"

Larry
--AaB03x
Content-Disposition: form-data; name="files"
Content-Type: multipart/mixed; boundary=BbC04y

--BbC04y
Content-Disposition: file; filename="file1.txt"
Content-Type: text/plain

... contents of file1.txt ...
--BbC04y
Content-Disposition: file; filename="file2.gif"
Content-Type: image/gif
Content-Transfer-Encoding: binary

...contents of file2.gif...
--BbC04y--
--AaB03x--
"""
